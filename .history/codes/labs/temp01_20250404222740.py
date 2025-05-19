import os
import glob
import markdown
import re
from pathlib import Path

# 指定目录路径
directory = r"C:\Users\520wo\Desktop\mdx"
output_dir = r"C:\Users\520wo\Desktop\mdx_markdown"
combined_file = r"C:\Users\520wo\Desktop\combined_markdown.md"

# 创建输出目录(如果不存在)
os.makedirs(output_dir, exist_ok=True)

# 获取所有文件
all_files = []
for root, dirs, files in os.walk(directory):
    for file in files:
        all_files.append(os.path.join(root, file))

# 转换每个文件为Markdown并写入单独文件
markdown_contents = []
for file_path in all_files:
    file_name = os.path.basename(file_path)
    output_path = os.path.join(
        output_dir, f"{os.path.splitext(file_name)[0]}.md")

    # 读取文件内容
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 根据文件类型进行转换
        ext = os.path.splitext(file_path)[1].lower()

        # HTML文件转换
        if ext == '.html':
            # 简单提取HTML内容
            content = re.sub(r'<[^>]+>', '', content)
        # 如果已经是Markdown文件，保持不变
        elif ext == '.md' or ext == '.markdown':
            pass
        # 其他文件类型，添加代码块格式
        else:
            content = f"# {file_name}\n\n```{ext[1:]}\n{content}\n```\n"

        # 添加文件标题
        md_content = f"# {file_name}\n\n{content}\n\n---\n\n"

        # 写入单独的Markdown文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(md_content)

        # 添加到组合内容
        markdown_contents.append(md_content)

    except Exception as e:
        print(f"处理文件 {file_path} 时出错: {e}")

# 合并所有Markdown内容到一个文件
with open(combined_file, 'w', encoding='utf-8') as f:
    f.write("# 合并的Markdown文档\n\n")
    f.write("## 目录\n\n")

    # 创建目录
    for i, file_path in enumerate(all_files):
        file_name = os.path.basename(file_path)
        f.write(
            f"{i+1}. [{file_name}](#{file_name.replace(' ', '-').replace('.', '').lower()})\n")

    f.write("\n---\n\n")
    f.write("".join(markdown_contents))

print(f"已将所有文件转换为Markdown并合并到: {combined_file}")
