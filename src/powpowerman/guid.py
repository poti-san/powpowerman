from ctypes import Structure, c_uint8
from types import NotImplementedType


class Guid(Structure):
    """GUID型。

    Examples:
        >>> iid_iunk1 = Guid.from_define(0x00000000, 0, 0, 0xC0, 0, 0, 0, 0, 0, 0, 0x46)
        >>> iid_iunk2 = Guid.from_str_d("00000000-0000-0000-C000-000000000046")
        >>> iid_iunk3 = Guid.from_str_b("{00000000-0000-0000-C000-000000000046}")
    """

    _fields_ = (("data", c_uint8 * 16),)

    __slots__ = ()

    @staticmethod
    def from_define(a: int, b: int, c: int, d: int, e: int, f: int, g: int, h: int, i: int, j: int, k: int) -> "Guid":
        """Windows SDKのDEFINE_GUIDマクロ形式からGuidを作成します。"""
        # c_uint32等を使った方がコードはきれいになりますが、
        # インスタンスの作成コストを回避するためにベタ書きで代入します。
        if not (0 <= a <= 0xFFFFFFFF) or not (0 <= b <= 0xFFFF) or not (0 <= c <= 0xFFFF):
            raise ValueError
        guid = Guid()
        data = guid.data
        # a (LE)
        data[0] = a & 0x000000FF
        data[1] = (a & 0x0000FF00) >> 8
        data[2] = (a & 0x00FF0000) >> 16
        data[3] = (a & 0xFF000000) >> 24
        # b (LE)
        data[4] = b & 0x00FF
        data[5] = (b & 0xFF00) >> 8
        # c (LE)
        data[6] = c & 0x00FF
        data[7] = (c & 0xFF00) >> 8
        # d-k
        data[8] = d
        data[9] = e
        data[10] = f
        data[11] = g
        data[12] = h
        data[13] = i
        data[14] = j
        data[15] = k
        return guid

    @staticmethod
    def from_parts_int(a: int, b: int, c: int, d: int, e: int) -> "Guid":
        """ "00000000-0000-0000-0000-000000000000"表現のハイフンで区切られた部分に対応する数値からGuidを作成します。"""
        if (
            not (0 <= a <= 0xFFFFFFFF)
            or not (0 <= b <= 0xFFFF)
            or not (0 <= c <= 0xFFFF)
            or not (0 <= d <= 0xFFFF)
            or not (0 <= e <= 0xFFFFFFFFFFFF)
        ):
            raise ValueError

        guid = Guid()
        data = guid.data
        # a (LE)
        data[0] = a & 0x000000FF
        data[1] = (a & 0x0000FF00) >> 8
        data[2] = (a & 0x00FF0000) >> 16
        data[3] = (a & 0xFF000000) >> 24
        # b (LE)
        data[4] = b & 0x00FF
        data[5] = (b & 0xFF00) >> 8
        # c (LE)
        data[6] = c & 0x00FF
        data[7] = (c & 0xFF00) >> 8
        # d (BE)
        data[8] = (d & 0xFF00) >> 8
        data[9] = d & 0x00FF
        # e (BE)
        data[10] = (e & 0xFF0000000000) >> 40
        data[11] = (e & 0x00FF00000000) >> 32
        data[12] = (e & 0x0000FF000000) >> 24
        data[13] = (e & 0x000000FF0000) >> 16
        data[14] = (e & 0x00000000FF00) >> 8
        data[15] = e & 0x0000000000FF
        return guid

    @staticmethod
    def from_parts_str(a: str, b: str, c: str, d: str, e: str) -> "Guid":
        """ "00000000-0000-0000-0000-000000000000"表現のハイフンで区切られた部分からGuidを作成します。"""
        # 内容はint(x, 16)で調べるので、長さだけ確認する。
        if len(a) != 8 or len(b) != 4 or len(c) != 4 or len(d) != 4 or len(e) != 12:
            raise ValueError
        return Guid.from_parts_int(int(a, 16), int(b, 16), int(c, 16), int(d, 16), int(e, 16))

    @staticmethod
    def from_str_d(s: str) -> "Guid":
        """ "00000000-0000-0000-0000-000000000000"表現からGuidを作成します。"""
        # 数値部分はGuid.from_strpartsが調べるので全体の長さとハイフンだけ確認する。
        if len(s) != 36 or s[8] != "-" or s[13] != "-" or s[18] != "-" or s[23] != "-":
            raise ValueError
        return Guid.from_parts_str(s[0:8], s[9:13], s[14:18], s[19:23], s[24:36])

    @staticmethod
    def from_str(s: str) -> "Guid":
        """ "{00000000-0000-0000-0000-000000000000}"表現からGuidを作成します。"""
        # 数値部分はGuid.from_strpartsが調べるので全体の長さとハイフンだけ確認する。
        if len(s) != 38 or s[0] != "{" or s[37] != "}" or s[9] != "-" or s[14] != "-" or s[19] != "-" or s[24] != "-":
            raise ValueError
        return Guid.from_parts_str(s[1:9], s[10:14], s[15:19], s[20:24], s[25:37])

    def __str__(self) -> str:
        """ "{00000000-0000-0000-0000-000000000000}"表現を返します。"""
        return self.to_str()

    def __repr__(self) -> str:
        """Guid({00000000-0000-0000-0000-000000000000})表現を返します。"""
        return f"Guid({self.to_str()})"

    def __hash__(self):
        """現在のハッシュを返します。ミュータブルなので変化する可能性があります。"""
        return hash(bytes(self))

    def __eq__(self, other) -> bool | NotImplementedType:
        if isinstance(other, Guid):
            return bytes(self) == bytes(other)
        return NotImplemented

    def __ne__(self, other) -> bool | NotImplementedType:
        if isinstance(other, Guid):
            return bytes(self) != bytes(other)
        return NotImplemented

    @property
    def parts(self) -> tuple[int, int, int, int, int]:
        """文字列表現"00000000-0000-0000-0000-000000000000"時のハイフンで区切られた各部分を返します。"""
        return (
            int.from_bytes(self.data[0:4], "little"),
            int.from_bytes(self.data[4:6], "little"),
            int.from_bytes(self.data[6:8], "little"),
            int.from_bytes(self.data[8:10], "big"),
            int.from_bytes(self.data[10:16], "big"),
        )

    def to_str_d(self) -> str:
        """ "00000000-0000-0000-0000-000000000000"表現を返します。"""
        a, b, c, d, e = self.parts
        return f"{a:0>8x}-{b:0>4x}-{c:0>4x}-{d:0>4x}-{e:0>12x}"

    def to_str(self) -> str:
        """ "{00000000-0000-0000-0000-000000000000}"表現を返します。"""
        a, b, c, d, e = self.parts
        return f"{{{a:0>8x}-{b:0>4x}-{c:0>4x}-{d:0>4x}-{e:0>12x}}}"
