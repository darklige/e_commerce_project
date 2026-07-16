# Commerce Android

M0 阶段提供 Android/Compose 工程骨架，后续用于实现普通用户购物端。

## 本地要求

- Android CLI 或 Android Studio
- JDK
- Gradle Wrapper
- Android SDK 35

本仓库包含 Gradle Wrapper，优先使用 Android Studio 内置 JBR 或本机 JDK 执行构建。

可运行：

```bash
cd apps/android
export JAVA_HOME="/Applications/Android Studio.app/Contents/jbr/Contents/Home"
export ANDROID_HOME="$HOME/Library/Android/sdk"
./gradlew lint test assembleDebug
```
