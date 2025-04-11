# 全ての電源設定のGUIDとAC値型を取得する。

from powpowerman import PowerScheme

scheme = PowerScheme.active_scheme()
for subgroup in scheme.iter_subgroups():
    for setting in subgroup.iter_settings():
        print(f"{setting.scheme_guid},{setting.subgroup_guid},{setting.setting_guid} ({repr(setting.ac_value_type)})")

pass
