# 全ての電源サブグループの情報を取得する。

from powpowerman import PowerScheme

for scheme in PowerScheme.enumerate():
    print(f"{scheme.friendlyname}: {scheme.description} ({scheme.scheme_guid})")
    for subgroup in scheme.iter_subgroups():
        print(f"  {subgroup.friendlyname}: {subgroup.description} ({subgroup.subgroup_guid})")

pass
