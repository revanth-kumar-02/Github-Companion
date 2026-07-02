"""README generation service for GitHub Companion."""
import os


def generate_readme(data: dict, output_folder: str) -> str:
    """
    Generate a professional README.md from structured project data.

    Args:
        data: dict with keys: name, description, features, installation,
              usage, technologies, license, author
        output_folder: absolute path to write README.md into

    Returns:
        Absolute path to the generated README.md file.
    """
    features_md = _format_list(data.get("features", []))
    technologies_md = _format_list(data.get("technologies", []))

    readme_content = f"""# {data['name']}

> {data['description']}

---

## ✨ Features

{features_md}

---

## 🛠️ Technologies Used

{technologies_md}

---

## ⚙️ Installation

```bash
{data.get('installation', 'Add installation steps here.')}
```

---

## 🚀 Usage

```bash
{data.get('usage', 'Add usage examples here.')}
```

---

## 📄 License

This project is licensed under the **{data.get('license', 'MIT')} License**.

---

## 👤 Author

**{data.get('author', 'Unknown')}**

---

*Generated with [GitHub Companion](https://github.com) CLI*
"""

    output_path = os.path.join(output_folder, "README.md")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(readme_content)

    return output_path


def _format_list(items: list) -> str:
    """Convert a list of strings into a markdown bullet list."""
    if not items:
        return "- N/A"
    return "\n".join(f"- {item}" for item in items)
