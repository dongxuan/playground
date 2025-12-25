#!/bin/bash
# TestCase Generator Script (Demo Version)
# 为指定文件或目录生成测试用例

# 检查参数
if [ $# -eq 0 ]; then
    echo "用法: $0 <文件或目录路径>"
    exit 1
fi

TARGET="$1"

# 检查路径是否存在
if [ ! -e "$TARGET" ]; then
    echo "错误: 路径不存在: $TARGET"
    exit 1
fi

# 处理单个文件的函数
process_file() {
    local file="$1"
    local dir=$(dirname "$file")
    local filename=$(basename "$file")
    local name="${filename%.*}"
    local ext="${filename##*.}"

    # 如果没有扩展名
    if [ "$name" == "$filename" ]; then
        local testfile="${dir}/${name}-test"
    else
        local testfile="${dir}/${name}-test.${ext}"
    fi

    # 复制文件作为测试用例
    cp "$file" "$testfile"
    echo "✓ 已生成: $testfile"
}

# 如果是文件
if [ -f "$TARGET" ]; then
    echo "处理文件: $TARGET"
    process_file "$TARGET"
    echo "完成!"
    exit 0
fi

# 如果是目录
if [ -d "$TARGET" ]; then
    echo "处理目录: $TARGET"
    count=0

    # 遍历目录中的所有文件
    while IFS= read -r -d '' file; do
        # 跳过已经是测试文件的
        if [[ "$file" == *"-test."* ]] || [[ "$file" == *"-test" ]]; then
            continue
        fi

        process_file "$file"
        ((count++))
    done < <(find "$TARGET" -type f -print0)

    echo "完成! 共处理 $count 个文件"
    exit 0
fi

echo "错误: $TARGET 既不是文件也不是目录"
exit 1
