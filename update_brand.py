import os

old_text = "Jenny 筱筑 CFP®"
new_text = "JennyHsieh CFP®"

root_dir = os.path.dirname(os.path.abspath(__file__))
count = 0

for dirpath, _, filenames in os.walk(root_dir):
    # 略過虛擬環境與快取資料夾
    if ".venv" in dirpath or "__pycache__" in dirpath:
        continue
    for file in filenames:
        if file.endswith(".py") and file != "update_brand.py":
            filepath = os.path.join(dirpath, file)
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            if old_text in content:
                updated_content = content.replace(old_text, new_text)
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(updated_content)
                print(f"✅ 已成功更新：{file}")
                count += 1

print(f"\n🎉 全部完成！共已自動更新 {count} 個檔案。")
