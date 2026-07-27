# 稼轩桌面宠物

一个以德国牧羊犬“稼轩”为原型制作的 Windows 桌面宠物。

## 当前功能

- 透明背景、置顶显示
- 可拖动到桌面任意位置
- 鼠标靠近时朝鼠标方向观察
- 单击时跳跃
- 待机时从 4 组开心互动动作中随机选择 1 组播放
- 鼠标长时间离开后播放委屈动画
- 左右移动与跑动动画
- 右键菜单退出
- 退出时显示“稼轩还想下次继续和你玩哦~”

## 直接运行

下载 `dist/ShepherdPet-alpha.exe`，在 Windows 中双击即可运行，不需要安装 GPT。

退出程序：右键点击桌面宠物，选择“退出”。

## 项目结构

- `ShepherdPetAlpha/app.py`：桌面宠物主程序与交互逻辑
- `ShepherdPetAlpha/assets/`：程序图标、动画清单和预处理后的 BGRA 帧
- `prepare_raw_assets.py`：从精灵图生成程序所用动画帧
- `qa/`：委屈动画的逐帧图片与 GIF 预览
- `dist/ShepherdPet-alpha.exe`：当前可运行版本

## 从源代码运行

主程序只依赖 Python 标准库和 Windows API：

```powershell
python .\ShepherdPetAlpha\app.py
```

如需重新生成动画素材，先安装 Pillow：

```powershell
python -m pip install Pillow
python .\prepare_raw_assets.py
```

## 打包 EXE

安装 PyInstaller：

```powershell
python -m pip install pyinstaller
```

然后在本目录运行：

```powershell
python -m PyInstaller --noconfirm --clean --windowed --onefile `
  --name ShepherdPet-alpha `
  --icon .\ShepherdPetAlpha\assets\app.ico `
  --add-data ".\ShepherdPetAlpha\assets;assets" `
  .\ShepherdPetAlpha\app.py
```

## 隐私与使用

本仓库包含以私人宠物照片制作的动画素材，默认作为私人项目保存。未经主人许可，请勿将素材用于商业用途或重新发布。
