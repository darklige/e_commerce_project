# Commerce Android

M0 阶段提供 Android/Compose 工程骨架，后续用于实现普通用户购物端。

## 本地要求

- Android CLI 或 Android Studio
- JDK
- Gradle 或 Gradle Wrapper
- Android SDK 35

当前开发机缺少 `android` CLI、Java Runtime 和 Gradle，因此本阶段只能完成文件级骨架，暂不能在本机编译验证。

安装工具链后可运行：

```bash
gradle -p apps/android :app:assembleDebug
```

