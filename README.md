# powpowermanパッケージ

PythonからWindowsの電力管理機能を使いやすくするパッケージです。標準ライブラリとpowguidパッケージに依存します。

次のようなコードが簡単に書けます。

**アクティブな電力スキームのディスプレイ設定列挙**

```python
from powpowerman import PowerScheme

for setting in PowerScheme.active_scheme().subgroup_display.iter_settings():
    print(f"{setting.friendlyname} ({setting.setting_guid})")
```

**画面の明るさを50%に設定**

```python
from powguid import Guid

from powpowerman import PowerScheme

GUID_DISPLAY_BRIGHTNESS_LEVEL = Guid.from_str("{aded5e82-b909-4619-9949-f5d71dac0bcb}")

display_subgroup = PowerScheme.active_scheme().subgroup_display
display_brightness = display_subgroup.settings(GUID_DISPLAY_BRIGHTNESS_LEVEL)
display_brightness.ac_value_index = 50
# display_brightness.ac_value_index = 100

display_brightness.apply_changes()
```
