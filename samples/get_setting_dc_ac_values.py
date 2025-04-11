# アクティブな電源スキームのサブグループ下電源設定のDC値・AC値を取得する。

from powpowerman import PowerScheme

scheme = PowerScheme.active_scheme()
print(f"{scheme.friendlyname}: {scheme.description} ({scheme.scheme_guid})")

for subgroup in scheme.iter_subgroups():
    print(f"{subgroup.friendlyname or "<ERROR>"} ({subgroup.description})")
    for setting in subgroup.iter_settings():
        print(
            f"  {setting.friendlyname} ({setting.setting_guid}): "
            f"DC {repr(setting.dc_value)}, AC {repr(setting.ac_value)}"
        )

pass
