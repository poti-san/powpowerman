# 全ての電源設定の設定値情報を取得する。

from powpowerman import PowerScheme

for scheme in PowerScheme.enumerate():
    print(f"{scheme.friendlyname}: {scheme.description} ({scheme.scheme_guid})")
    for subgroup in scheme.iter_subgroups():
        for setting in subgroup.iter_settings():
            possible_setting = setting.as_possible_setting
            print(tuple(possible_setting.descriptions))

pass
