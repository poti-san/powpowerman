from powpowerman import PowerScheme

for setting in PowerScheme.active_scheme().subgroup_battery.iter_settings():
    print(f"{setting.friendlyname} ({setting.setting_guid})")

pass
