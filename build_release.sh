#!/bin/bash
# PyUpdater 构建和发布脚本

# 设置版本号(从 app/version.py 读取)
VERSION=$(python3 -c "from app.version import __version__; print(__version__)")

echo "======================================"
echo "PyUpdater 构建脚本"
echo "当前版本: $VERSION"
echo "======================================"

# 步骤1: 初始化 PyUpdater (首次运行)
init_pyupdater() {
    echo "初始化 PyUpdater..."
    pyupdater init
}

# 步骤2: 构建应用
build_app() {
    echo "开始构建应用..."
    pyupdater build --app-version=$VERSION build.spec
}

# 步骤3: 生成密钥 (首次运行)
generate_keys() {
    echo "生成密钥..."
    pyupdater keys --create
}

# 步骤4: 打包更新
package_update() {
    echo "打包更新..."
    pyupdater pkg --process --sign
}

# 步骤5: 上传到 GitHub Release
upload_to_github() {
    echo "准备上传到 GitHub Release..."

    # 检查 gh CLI 是否安装
    if ! command -v gh &> /dev/null; then
        echo "错误: GitHub CLI (gh) 未安装"
        echo "请访问 https://cli.github.com/ 安装"
        exit 1
    fi

    # 创建 Release
    echo "创建 GitHub Release v$VERSION..."
    gh release create "v$VERSION" \
        --title "v$VERSION" \
        --notes "Release v$VERSION" \
        pyu-data/deploy/*.zip \
        pyu-data/deploy/*.gz

    echo "上传完成！"
}

# 主流程
case "$1" in
    init)
        init_pyupdater
        generate_keys
        ;;
    build)
        build_app
        ;;
    package)
        package_update
        ;;
    upload)
        upload_to_github
        ;;
    all)
        build_app
        package_update
        upload_to_github
        ;;
    *)
        echo "用法: $0 {init|build|package|upload|all}"
        echo ""
        echo "  init    - 初始化 PyUpdater (首次运行)"
        echo "  build   - 构建应用"
        echo "  package - 打包更新"
        echo "  upload  - 上传到 GitHub Release"
        echo "  all     - 执行完整流程 (build + package + upload)"
        exit 1
        ;;
esac

echo "======================================"
echo "操作完成！"
echo "======================================"
