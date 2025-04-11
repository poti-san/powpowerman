# アクティブな電源スキーム直下の電源設定情報を取得する。

from powpowerman import PowerScheme

for setting in PowerScheme.active_scheme().nosubgroup.iter_settings():
    print(f"{setting.friendlyname} ({setting.setting_guid})")
