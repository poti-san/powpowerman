from powpowerman import PowerScheme

for setting in PowerScheme.active_scheme().nosubgroup.iter_settings():
    print(f"{setting.friendlyname} ({setting.setting_guid})")
