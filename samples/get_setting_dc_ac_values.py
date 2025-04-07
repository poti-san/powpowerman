from powpowerman import PowerScheme

scheme = PowerScheme.active_scheme()
print(f"{scheme.friendlyname}: {scheme.description} ({scheme.scheme_guid})")

for subgroup in scheme.iter_subgroups():
    subgroup_friendlyname = subgroup.friendlyname
    subgroup_description = subgroup.description
    print(f"{subgroup_friendlyname or "<ERROR>"} ({subgroup.subgroup_guid})")

    for setting in subgroup.iter_settings():
        print(
            f"  {setting.friendlyname} ({setting.setting_guid}): "
            f"DC {repr(setting.dc_value)}, AC {repr(setting.ac_value)}"
        )

pass
