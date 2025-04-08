from ctypes import (
    POINTER,
    WinDLL,
    WinError,
    byref,
    c_byte,
    c_int32,
    c_uint32,
    c_void_p,
    sizeof,
)
from dataclasses import dataclass
from enum import IntEnum
from os.path import expandvars
from types import NotImplementedType
from typing import Iterator
from typing import cast as typecast

from .guid import Guid


class PowerSettingValueType(IntEnum):
    """電力設定の値型。"""

    NONE = 0
    STR = 1
    EXPAND_STR = 2
    BINARY = 3
    UINT32 = 4
    UINT32_LE = 4
    UINT32_BE = 5
    LINK = 6
    MULTI_STR = 7
    RESOURCE_LIST = 8
    FULL_RESOURCE_DESCRIPTOR = 9
    RESOURCE_REQUIREMENTS_LIST = 10
    UINT64 = 11
    UINT64_LE = 11


class PowerKnownSubGroupGuid:
    """電力の既知サブグループGUID。"""

    NO = Guid.from_str_d("fea3413e-7e05-4911-9a71-700331f1c294")
    DISK = Guid.from_str_d("0012ee47-9041-4b5d-9b77-535fba8b1442")
    SYSTEM_BUTTON = Guid.from_str_d("4f971e89-eebd-4455-a8de-9e59040e7347")
    PROCESSOR_SETTINGS = Guid.from_str_d("54533251-82be-4824-96c1-47b60b740d00")
    # NOTE: SDK上ではVIDEOですが、実態に合わせてDISPLAYとします。
    DISPLAY = Guid.from_str_d("7516b95f-f776-4464-8c53-06167f40cc99")
    BATTERY = Guid.from_str_d("e73a048d-bf27-4f12-9731-8b2076e8891f")
    SLEEP = Guid.from_str_d("238C9FA8-0AAD-41ED-83F4-97BE242C8F20")
    PCIEXPRESS_SETTINGS = Guid.from_str_d("501a4d13-42af-4429-9fd1-a8218c268e20")


@dataclass(frozen=True)
class PowerSettingValue:
    """電力設定の値。イミュータブルです。"""

    type: PowerSettingValueType | int
    raw: bytes

    @property
    def value(self) -> object:
        """型に対応する値。"""
        match self.type:
            case PowerSettingValueType.NONE:
                return None
            case PowerSettingValueType.STR:
                return self.raw[:-2].decode("utf-16le")
            case PowerSettingValueType.EXPAND_STR:
                return expandvars(self.raw[:-2].decode("utf-16le"))
            case PowerSettingValueType.BINARY:
                return self.raw
            case PowerSettingValueType.UINT32_LE:
                return int.from_bytes(self.raw[0:4], "little")
            case PowerSettingValueType.UINT32_BE:
                return int.from_bytes(self.raw[0:4], "big")
            # LINK = 6
            case PowerSettingValueType.MULTI_STR:
                return self.raw[:-4].decode("utf-16le").split("\0")
            # RESOURCE_LIST = 8
            # FULL_RESOURCE_DESCRIPTOR = 9
            # RESOURCE_REQUIREMENTS_LIST = 10
            case PowerSettingValueType.UINT64_LE:
                return int.from_bytes(self.raw[0:8], "little")
            case _:
                return self.raw

    def __str__(self) -> str:
        return str(self.value)

    def __repr__(self) -> str:
        return f"{self.__str__()} ({repr(self.type)})"


class PowerEntry:
    """電力情報の基本クラス。実際にはPowerScheme、PowerSubGroup、PowerSettingクラスを使用します。"""

    _scheme_guid: Guid | None
    _subgroup_guid: Guid | None
    _setting_guid: Guid | None

    __slots__ = ("_scheme_guid", "_subgroup_guid", "_setting_guid")

    def __init__(self, scheme_guid: Guid | None, subgroup_guid: Guid | None, setting_guid: Guid | None) -> None:
        self._scheme_guid = scheme_guid
        self._subgroup_guid = subgroup_guid
        self._setting_guid = setting_guid

    def __eq__(self, other) -> bool | NotImplementedType:
        """電源スキーム、電源サブグループ及び電源設定の各GUIDがすべて一致すれば真を返します。"""
        if isinstance(other, PowerEntry):
            return (
                self._scheme_guid == other._scheme_guid
                and self._subgroup_guid == other._subgroup_guid
                and self._setting_guid == other._setting_guid
            )
        return NotImplemented

    def __ne__(self, other) -> bool | NotImplementedType:
        """電源スキーム、電源サブグループ及び電源設定の各GUIDがいずれかが不一致なら真を返します。"""
        if isinstance(other, PowerEntry):
            return (
                self._scheme_guid != other._scheme_guid
                or self._subgroup_guid != other._subgroup_guid
                or self._setting_guid != other._setting_guid
            )
        return NotImplemented

    @property
    def scheme_guid_ref(self):
        """byref(scheme_guid)を返します。"""
        return byref(self._scheme_guid) if self._scheme_guid else None

    @property
    def subgroup_guid_ref(self):
        """byref(subgroup_guid)を返します。"""
        return byref(self._subgroup_guid) if self._subgroup_guid else None

    @property
    def setting_guid_ref(self):
        """byref(setting_guid)を返します。"""
        return byref(self._setting_guid) if self._setting_guid else None

    @property
    def friendlyname(self) -> str | None:
        bufsize = c_uint32()
        ret = _PowerReadFriendlyName(
            None, self.scheme_guid_ref, self.subgroup_guid_ref, self.setting_guid_ref, None, byref(bufsize)
        )
        """電力スキーム、サブグループまたは設定のフレンドリー名を取得します。エラー時はNoneを返します。"""

        if ret != 0:
            return None
        buf = (c_byte * bufsize.value)()
        ret = _PowerReadFriendlyName(
            None, self.scheme_guid_ref, self.subgroup_guid_ref, self.setting_guid_ref, buf, byref(bufsize)
        )
        return bytes(memoryview(buf)[:-2]).decode("utf-16le")

    @property
    def description(self) -> str | None:
        bufsize = c_uint32()
        ret = _PowerReadDescription(
            None, self.scheme_guid_ref, self.subgroup_guid_ref, self.setting_guid_ref, None, byref(bufsize)
        )
        """電力スキーム、サブグループまたは設定の説明を取得します。エラー時はNoneを返します。"""

        if ret != 0:
            return None
        buf = (c_byte * bufsize.value)()
        ret = _PowerReadDescription(
            None, self.scheme_guid_ref, self.subgroup_guid_ref, self.setting_guid_ref, buf, byref(bufsize)
        )
        return bytes(memoryview(buf)[:-2]).decode("utf-16le")

    @property
    def iconres_specifier(self) -> str | None:
        bufsize = c_uint32()
        ret = _PowerReadIconResourceSpecifier(
            None, self.scheme_guid_ref, self.subgroup_guid_ref, self.setting_guid_ref, None, byref(bufsize)
        )
        """電力スキーム、サブグループまたは設定のアイコンリソースを取得します。エラー時はNoneを返します。"""

        if ret != 0:
            return None
        buf = (c_byte * bufsize.value)()
        ret = _PowerReadIconResourceSpecifier(
            None, self.scheme_guid_ref, self.subgroup_guid_ref, self.setting_guid_ref, buf, byref(bufsize)
        )
        return bytes(memoryview(buf)[:-2]).decode("utf-16le")


class PowerSetting(PowerEntry):
    """電力設定。"""

    __slots__ = ()

    def __init__(self, scheme_guid: Guid, subgroup_guid: Guid, setting_guid: Guid) -> None:
        super().__init__(scheme_guid, subgroup_guid, setting_guid)

    @property
    def scheme(self) -> "PowerScheme":
        return PowerScheme(self.scheme_guid)

    @property
    def subgroup(self) -> "PowerSubGroup":
        return PowerSubGroup(self.scheme_guid, self.subgroup_guid)

    @property
    def scheme_guid(self) -> Guid:
        return typecast(Guid, self._scheme_guid)

    @property
    def subgroup_guid(self) -> Guid:
        return typecast(Guid, self._subgroup_guid)

    @property
    def setting_guid(self) -> Guid:
        return typecast(Guid, self._setting_guid)

    @property
    def as_possible_setting(self):
        """設定の取り得る値を取得します。"""
        return PowerPossibleSetting(self.subgroup_guid, self.setting_guid)

    @property
    def dc_value(self) -> PowerSettingValue | None:
        bufsize = c_uint32()
        ret = _PowerReadDCValue(
            None, self.scheme_guid_ref, self.subgroup_guid_ref, self.setting_guid_ref, None, None, byref(bufsize)
        )
        """直流電源時（バッテリー稼働時）の値を取得します。エラー時はNoneを返します。"""

        if ret != 0:
            return None
        buf = (c_byte * bufsize.value)()
        buftype = c_uint32()
        ret = _PowerReadDCValue(
            None,
            self.scheme_guid_ref,
            self.subgroup_guid_ref,
            self.setting_guid_ref,
            byref(buftype),
            buf,
            byref(bufsize),
        )
        if ret != 0:
            return None
        return PowerSettingValue(PowerSettingValueType(buftype.value), bytes(buf))

    @property
    def ac_value(self) -> PowerSettingValue | None:
        bufsize = c_uint32()
        ret = _PowerReadACValue(
            None, self.scheme_guid_ref, self.subgroup_guid_ref, self.setting_guid_ref, None, None, byref(bufsize)
        )
        """交流電源時（コンセント接続時）の値を取得します。エラー時はNoneを返します。"""

        if ret != 0:
            return None
        buf = (c_byte * bufsize.value)()
        buftype = c_uint32()
        ret = _PowerReadACValue(
            None,
            self.scheme_guid_ref,
            self.subgroup_guid_ref,
            self.setting_guid_ref,
            byref(buftype),
            buf,
            byref(bufsize),
        )
        if ret != 0:
            return None
        return PowerSettingValue(PowerSettingValueType(buftype.value), bytes(buf))

    @property
    def dc_value_type(self) -> PowerSettingValueType | int | None:
        """直流電源時（バッテリー稼働時）の値の型を取得します。エラー時はNoneを返します。"""
        bufsize = c_uint32()
        valuetype = c_uint32()
        ret = _PowerReadDCValue(
            None,
            self.scheme_guid_ref,
            self.subgroup_guid_ref,
            self.setting_guid_ref,
            byref(valuetype),
            None,
            byref(bufsize),
        )
        return valuetype.value if ret == 0 else None

    @property
    def dc_value_size(self) -> PowerSettingValueType | int | None:
        """直流電源時（バッテリー稼働時）の値のバイト数を取得します。エラー時はNoneを返します。"""
        bufsize = c_uint32()
        ret = _PowerReadDCValue(
            None,
            self.scheme_guid_ref,
            self.subgroup_guid_ref,
            self.setting_guid_ref,
            None,
            None,
            byref(bufsize),
        )
        return bufsize.value if ret == 0 else None

    @property
    def ac_value_type(self) -> PowerSettingValueType | int | None:
        """交流電源時（コンセント接続時）の値の型を取得します。エラー時はNoneを返します。"""
        bufsize = c_uint32()
        valuetype = c_uint32()
        ret = _PowerReadACValue(
            None,
            self.scheme_guid_ref,
            self.subgroup_guid_ref,
            self.setting_guid_ref,
            byref(valuetype),
            None,
            byref(bufsize),
        )
        return valuetype.value if ret == 0 else None

    @property
    def ac_value_size(self) -> PowerSettingValueType | int | None:
        """交流電源時（コンセント接続時）の値のバイト数を取得します。エラー時はNoneを返します。"""
        bufsize = c_uint32()
        ret = _PowerReadACValue(
            None,
            self.scheme_guid_ref,
            self.subgroup_guid_ref,
            self.setting_guid_ref,
            None,
            None,
            byref(bufsize),
        )
        return bufsize.value if ret == 0 else None

    @property
    def dc_value_index(self) -> int | None:
        """直流電源時（バッテリー稼働時）の値インデックスを取得または設定します。エラー時はNoneを返します。

        設定される値はvalue_typeやPowerPossibleSettingを確認してください。"""
        x = c_uint32()
        ret = _PowerReadDCValueIndex(
            None, self.scheme_guid_ref, self.subgroup_guid_ref, self.setting_guid_ref, byref(x)
        )
        return x.value if ret == 0 else None

    @property
    def ac_value_index(self) -> int | None:
        """交流電源時（コンセント接続時）の値インデックスを取得または設定します。エラー時はNoneを返します。

        設定される値はvalue_typeやPowerPossibleSettingを確認してください。"""
        x = c_uint32()
        ret = _PowerReadACValueIndex(
            None, self.scheme_guid_ref, self.subgroup_guid_ref, self.setting_guid_ref, byref(x)
        )
        return x.value if ret == 0 else None

    @dc_value_index.setter
    def dc_value_index(self, value: int) -> None:
        _PowerWriteDCValueIndex(None, self.scheme_guid_ref, self.subgroup_guid_ref, self.setting_guid_ref, value)

    @ac_value_index.setter
    def ac_value_index(self, value: int) -> None:
        _PowerWriteACValueIndex(None, self.scheme_guid_ref, self.subgroup_guid_ref, self.setting_guid_ref, value)

    def apply_changes(self) -> bool:
        """スキームがアクティブな場合に変更を反映します。成否を返します。"""
        scheme = self.scheme
        if not scheme or not scheme.is_active:
            return False
        return scheme.set_active()


class PowerSubGroup(PowerEntry):
    """電力サブグループ。"""

    __slots__ = ()

    def __init__(self, scheme_guid: Guid, subgroup_guid: Guid) -> None:
        super().__init__(scheme_guid, subgroup_guid, None)

    def __repr__(self) -> str:
        return f'PowerSubGroup("{self.friendlyname}" ({self.subgroup_guid} in {self.scheme_guid}))'

    @property
    def scheme(self) -> "PowerScheme":
        return PowerScheme(self.scheme_guid)

    @property
    def scheme_guid(self) -> Guid:
        return typecast(Guid, self._scheme_guid)

    @property
    def subgroup_guid(self) -> Guid:
        return typecast(Guid, self._subgroup_guid)

    def iter_settings(self) -> Iterator[PowerSetting]:
        """電力サブグループに所属する電力設定のイテレーターを返します。"""
        ERROR_NO_MORE_ITEMS = 259

        buf = Guid()
        bufsize = sizeof(Guid)
        for i in range(0xFFFFFFFF):
            cur_bufsize = c_uint32(bufsize)
            ret = _PowerEnumerate(
                None,
                self.scheme_guid_ref,
                self.subgroup_guid_ref,
                _ACCESS_INDIVIDUAL_SETTING,
                i,
                byref(buf),
                byref(cur_bufsize),
            )
            if ret == 0:
                yield PowerSetting(self.scheme_guid, self.subgroup_guid, buf)
            elif ret == ERROR_NO_MORE_ITEMS:
                break
            else:
                raise WinError(ret)

    def settings(self, setting_guid: Guid) -> PowerSetting:
        """GUIDを指定して電力設定を取得します。"""
        return PowerSetting(self.scheme_guid, self.subgroup_guid, setting_guid)


class PowerScheme(PowerEntry):
    """電力スキーム。"""

    __slots__ = ()

    def __init__(self, scheme_guid: Guid | None) -> None:
        super().__init__(scheme_guid, None, None)

    def __str__(self) -> str:
        return self.__repr__()

    def __repr__(self) -> str:
        return f'PowerScheme("{self.friendlyname}" ({self.scheme_guid}))'

    @property
    def scheme_guid(self) -> Guid:
        return typecast(Guid, self._scheme_guid)

    @staticmethod
    def enumerate() -> "Iterator[PowerScheme]":
        """電力スキームのイテレーターを返します。"""
        ERROR_NO_MORE_ITEMS = 259

        buf = Guid()
        bufsize = sizeof(Guid)
        for i in range(0xFFFFFFFF):
            cur_bufsize = c_uint32(bufsize)
            ret = _PowerEnumerate(None, None, None, _ACCESS_SCHEME, i, byref(buf), byref(cur_bufsize))
            if ret == 0:
                yield PowerScheme(buf)
            elif ret == ERROR_NO_MORE_ITEMS:
                break
            else:
                raise WinError(ret)

    def iter_subgroups(self) -> Iterator[PowerSubGroup]:
        """電力スキームに所属する電力サブグループのイテレーターを返します。"""
        ERROR_NO_MORE_ITEMS = 259

        buf = Guid()
        bufsize = sizeof(Guid)
        for i in range(0xFFFFFFFF):
            cur_bufsize = c_uint32(bufsize)
            ret = _PowerEnumerate(None, self.scheme_guid_ref, None, _ACCESS_SUBGROUP, i, byref(buf), byref(cur_bufsize))
            if ret == 0:
                yield PowerSubGroup(self.scheme_guid, buf)
            elif ret == ERROR_NO_MORE_ITEMS:
                break
            else:
                raise WinError(ret)

    def iter_settings(self) -> Iterator[PowerSetting]:
        """電力スキームに直接所属する電力設定のイテレーターを返します。

        次の操作と同じです。
        >>> power_scheme.nosubgroup.iter_settings()
        """
        return self.nosubgroup.iter_settings()

    @staticmethod
    def active_scheme() -> "PowerScheme":
        """アクティブな電力スキームを返します。"""
        p = POINTER(Guid)()
        ret = _PowerGetActiveScheme(None, byref(p))
        try:
            if ret != 0:
                raise WinError(ret)
            return PowerScheme(Guid.from_buffer_copy(p.contents))
        finally:
            _LocalFree(p)

    def is_active(self) -> bool:
        """電力スキームが現在アクティブであればTrueを返します。"""
        return self == PowerScheme.active_scheme()

    def set_active(self) -> bool:
        """電力スキームをアクティブに設定して、成否を返します。"""
        return _PowerSetActiveScheme(None, self.scheme_guid) == 0

    def subgroups(self, subgroup_guid: Guid) -> PowerSubGroup:
        """GUIDを指定して電力サブグループを取得します。"""
        return PowerSubGroup(self.scheme_guid, subgroup_guid)

    def settings(self, subgroup_guid: Guid, setting_guid: Guid) -> PowerSetting:
        """電力サブグループと電力設定のGUIDをそれぞれ指定して電力設定を取得します。"""
        return PowerSetting(self.scheme_guid, subgroup_guid, setting_guid)

    @property
    def nosubgroup(self) -> PowerSubGroup:
        """電力スキーム直下の電力設定を保持する電力サブグループを返します。"""
        return PowerSubGroup(self.scheme_guid, PowerKnownSubGroupGuid.NO)

    @property
    def subgroup_disk(self) -> PowerSubGroup:
        """ディスクを表す電力サブグループを返します。"""
        return PowerSubGroup(self.scheme_guid, PowerKnownSubGroupGuid.DISK)

    @property
    def subgroup_sysbutton(self) -> PowerSubGroup:
        """システムボタンを表す電力サブグループを返します。"""
        return PowerSubGroup(self.scheme_guid, PowerKnownSubGroupGuid.SYSTEM_BUTTON)

    @property
    def subgroup_processorsettings(self) -> PowerSubGroup:
        """プロセッサー設定を表す電力サブグループを返します。"""
        return PowerSubGroup(self.scheme_guid, PowerKnownSubGroupGuid.PROCESSOR_SETTINGS)

    @property
    def subgroup_display(self) -> PowerSubGroup:
        """画面やビデオを表す電力サブグループを返します。"""
        return PowerSubGroup(self.scheme_guid, PowerKnownSubGroupGuid.DISPLAY)

    @property
    def subgroup_battery(self) -> PowerSubGroup:
        """バッテリーを表す電力サブグループを返します。"""
        return PowerSubGroup(self.scheme_guid, PowerKnownSubGroupGuid.BATTERY)

    @property
    def subgroup_sleep(self) -> PowerSubGroup:
        """スリープ設定を表す電力サブグループを返します。"""
        return PowerSubGroup(self.scheme_guid, PowerKnownSubGroupGuid.SLEEP)

    @property
    def subgroup_pciexpress_settings(self) -> PowerSubGroup:
        """PCI EXPRESSを表す電力サブグループを返します。"""
        return PowerSubGroup(self.scheme_guid, PowerKnownSubGroupGuid.PCIEXPRESS_SETTINGS)


class PowerPossibleSetting:
    """電力設定の取り得る値。"""

    _subgroup_guid: Guid | None
    _setting_guid: Guid | None

    __slots__ = ("_subgroup_guid", "_setting_guid")

    def __init__(self, subgroup_guid: Guid | None, setting_guid: Guid | None) -> None:
        self._subgroup_guid = subgroup_guid
        self._setting_guid = setting_guid

    @property
    def subgroup_guid(self) -> Guid:
        return typecast(Guid, self._subgroup_guid)

    @property
    def setting_guid(self) -> Guid:
        return typecast(Guid, self._setting_guid)

    @property
    def _subgroup_guid_ref(self):
        return byref(self._subgroup_guid) if self._subgroup_guid else None

    @property
    def _setting_guid_ref(self):
        return byref(self._setting_guid) if self._setting_guid else None

    def get_description(self, index: int) -> str | None:
        """指定番目の説明を取得します。"""
        bufsize = c_uint32()
        ret = _PowerReadPossibleDescription(
            None, self._subgroup_guid_ref, self._setting_guid_ref, index, None, byref(bufsize)
        )
        if ret != 0:
            return None
        buf = (c_byte * bufsize.value)()
        ret = _PowerReadPossibleDescription(
            None, self._subgroup_guid_ref, self._setting_guid_ref, index, buf, byref(bufsize)
        )
        return bytes(memoryview(buf)[:-2]).decode("utf-16le")

    @property
    def descriptions(self) -> Iterator[str]:
        """説明を順番に返すイテレーターを取得します。"""

        ERROR_FILE_NOT_FOUND = 2

        for i in range(0xFFFFFFFF):
            bufsize = c_uint32()
            ret = _PowerReadPossibleDescription(
                None, self._subgroup_guid_ref, self._setting_guid_ref, i, None, byref(bufsize)
            )
            if ret != 0:
                if ret == ERROR_FILE_NOT_FOUND:
                    break
                raise WinError(ret)
            buf = (c_byte * bufsize.value)()
            ret = _PowerReadPossibleDescription(
                None, self._subgroup_guid_ref, self._setting_guid_ref, i, buf, byref(bufsize)
            )
            yield bytes(memoryview(buf)[:-2]).decode("utf-16le")


_ACCESS_SCHEME = 16
_ACCESS_SUBGROUP = 17
_ACCESS_INDIVIDUAL_SETTING = 18

_powerprof = WinDLL("powrprof.dll")

_PowerEnumerate = _powerprof.PowerEnumerate
_PowerEnumerate.restype = c_uint32
_PowerEnumerate.argtypes = (c_void_p, POINTER(Guid), POINTER(Guid), c_int32, c_uint32, c_void_p, POINTER(c_uint32))

_PowerReadFriendlyName = _powerprof.PowerReadFriendlyName
_PowerReadFriendlyName.restype = c_uint32
_PowerReadFriendlyName.argtypes = (
    c_void_p,
    POINTER(Guid),
    POINTER(Guid),
    POINTER(Guid),
    POINTER(c_byte),
    POINTER(c_uint32),
)

_PowerReadDescription = _powerprof.PowerReadDescription
_PowerReadDescription.restype = c_uint32
_PowerReadDescription.argtypes = (
    c_void_p,
    POINTER(Guid),
    POINTER(Guid),
    POINTER(Guid),
    POINTER(c_byte),
    POINTER(c_uint32),
)

_PowerReadIconResourceSpecifier = _powerprof.PowerReadIconResourceSpecifier
_PowerReadIconResourceSpecifier.restype = c_uint32
_PowerReadIconResourceSpecifier.argtypes = (
    c_void_p,
    POINTER(Guid),
    POINTER(Guid),
    POINTER(Guid),
    POINTER(c_byte),
    POINTER(c_uint32),
)

_PowerReadPossibleDescription = _powerprof.PowerReadPossibleDescription
_PowerReadPossibleDescription.restype = c_uint32
_PowerReadPossibleDescription.argtypes = (
    c_void_p,
    POINTER(Guid),
    POINTER(Guid),
    c_uint32,
    POINTER(c_byte),
    POINTER(c_uint32),
)

_PowerGetActiveScheme = _powerprof.PowerGetActiveScheme
_PowerGetActiveScheme.restype = c_uint32
_PowerGetActiveScheme.argtypes = (c_void_p, POINTER(POINTER(Guid)))

_PowerReadDCValue = _powerprof.PowerReadDCValue
_PowerReadDCValue.restype = c_int32
_PowerReadDCValue.argtypes = (
    c_void_p,
    POINTER(Guid),
    POINTER(Guid),
    POINTER(Guid),
    POINTER(c_uint32),
    POINTER(c_byte),
    POINTER(c_uint32),
)

_PowerReadACValue = _powerprof.PowerReadACValue
_PowerReadACValue.restype = c_int32
_PowerReadACValue.argtypes = (
    c_void_p,
    POINTER(Guid),
    POINTER(Guid),
    POINTER(Guid),
    POINTER(c_uint32),
    POINTER(c_byte),
    POINTER(c_uint32),
)

_PowerReadDCValueIndex = _powerprof.PowerReadDCValueIndex
_PowerReadDCValueIndex.restype = c_int32
_PowerReadDCValueIndex.argtypes = (c_void_p, POINTER(Guid), POINTER(Guid), POINTER(Guid), POINTER(c_uint32))

_PowerReadACValueIndex = _powerprof.PowerReadACValueIndex
_PowerReadACValueIndex.restype = c_int32
_PowerReadACValueIndex.argtypes = (c_void_p, POINTER(Guid), POINTER(Guid), POINTER(Guid), POINTER(c_uint32))

_PowerWriteDCValueIndex = _powerprof.PowerWriteDCValueIndex
_PowerWriteDCValueIndex.restype = c_int32
_PowerWriteDCValueIndex.argtypes = (c_void_p, POINTER(Guid), POINTER(Guid), POINTER(Guid), c_uint32)

_PowerWriteACValueIndex = _powerprof.PowerWriteACValueIndex
_PowerWriteACValueIndex.restype = c_int32
_PowerWriteACValueIndex.argtypes = (c_void_p, POINTER(Guid), POINTER(Guid), POINTER(Guid), c_uint32)

_PowerSetActiveScheme = _powerprof.PowerSetActiveScheme
_PowerSetActiveScheme.restype = c_int32
_PowerSetActiveScheme.argtypes = (c_void_p, POINTER(Guid))

_kernel32 = WinDLL("kernel32.dll")
_LocalFree = _kernel32.LocalFree
_LocalFree.restype = c_void_p
_LocalFree.argtypes = (c_void_p,)
