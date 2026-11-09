#!/usr/bin/env python3
"""
Renomeia o código-fonte do KBotExt para um novo nome, mantendo toda a funcionalidade.

Uso:
    python trocar_nome.py <pasta_do_codigo_original> <pasta_de_saida> <NovoNome> [usuario/repo_github]

Exemplo:
    python trocar_nome.py KBotExt-1.5.6 NexusKit NexusKit
    python trocar_nome.py KBotExt-1.5.6 NexusKit NexusKit meuusuario/NexusKit

- <NovoNome> deve ter só letras, números ou _ (vira nome do .exe, do projeto e da janela).
- [usuario/repo_github] é opcional: se informado, o aviso de "nova versão" passa a olhar
  as releases desse repositório. Se omitido, a checagem de atualização fica desligada
  (assim o app nunca manda você baixar o KBotExt original).
"""
import re
import shutil
import sys
from pathlib import Path

OLD = "KBotExt"


def die(msg):
    print("ERRO:", msg)
    sys.exit(1)


def read(p: Path) -> str:
    return p.read_bytes().decode("utf-8-sig")


def write(p: Path, text: str, bom=False):
    data = text.encode("utf-8")
    if bom:
        data = b"\xef\xbb\xbf" + data
    p.write_bytes(data)


def patch(p: Path, old: str, new: str, count_expected=None):
    raw = p.read_bytes()
    bom = raw.startswith(b"\xef\xbb\xbf")
    text = read(p)
    n = text.count(old)
    if n == 0:
        die(f"trecho não encontrado em {p.name}: {old[:60]!r}")
    if count_expected is not None and n != count_expected:
        die(f"esperava {count_expected} ocorrência(s) em {p.name}, achei {n}: {old[:60]!r}")
    write(p, text.replace(old, new), bom)


def main():
    if len(sys.argv) < 4:
        print(__doc__)
        sys.exit(1)
    src = Path(sys.argv[1]).resolve()
    out = Path(sys.argv[2]).resolve()
    name = sys.argv[3]
    repo = sys.argv[4] if len(sys.argv) > 4 else ""

    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{1,40}", name):
        die("o nome deve começar com letra e ter só letras, números ou _ (ex.: NexusKit)")
    if repo and not re.fullmatch(r"[\w.-]+/[\w.-]+", repo):
        die("repositório deve estar no formato usuario/repo")
    if not (src / f"{OLD}.sln").exists():
        die(f"{src} não parece ser a pasta do KBotExt (não achei {OLD}.sln)")
    if out.exists():
        die(f"{out} já existe; escolha outra pasta de saída")

    shutil.copytree(src, out)

    # 1) Renomear pasta do projeto e arquivos
    proj = out / OLD
    (out / f"{OLD}.sln").rename(out / f"{name}.sln")
    for suffix in [".vcxproj", ".vcxproj.filters", ".vcxproj.user", ".cpp"]:
        f = proj / f"{OLD}{suffix}"
        if f.exists():
            f.rename(proj / f"{name}{suffix}")
    proj.rename(out / name)
    proj = out / name

    # 2) Substituir o nome nos arquivos de projeto/build
    for f in [out / f"{name}.sln", proj / f"{name}.vcxproj", proj / f"{name}.vcxproj.filters",
              out / ".gitignore", out / ".github" / "workflows" / "build.yml"]:
        if f.exists():
            raw = f.read_bytes()
            bom = raw.startswith(b"\xef\xbb\xbf")
            write(f, read(f).replace(OLD, name), bom)

    # 3) Branding.h central (nome, título, repositório)
    write(proj / "Branding.h", f"""#pragma once

// ===== Identidade do aplicativo =====
// Edite aqui para mudar o nome que aparece na janela, no lobby, etc.
#define APP_NAME        "{name}"
#define APP_NAME_W      L"{name}"

// Repositório GitHub usado para avisar de novas versões ("usuario/repo").
// Deixe vazio ("") para desativar a checagem de atualização.
#define APP_GITHUB_REPO "{repo}"

// Nome usado ao criar lobbies personalizados / Practice Tool
#define APP_LOBBY_NAME  "{name}"

// Créditos do projeto original (licença GPL-3.0 exige manter o aviso)
#define APP_ORIGINAL_CREDIT "Baseado no KBotExt de KebsCS (github.com/KebsCS/KBotExt) - GPL-3.0"
""")
    # adiciona Branding.h e o .rc ao projeto
    vcx = proj / f"{name}.vcxproj"
    patch(vcx, '<ClInclude Include="Auth.h" />',
          '<ClInclude Include="Auth.h" />\n    <ClInclude Include="Branding.h" />', 1)
    patch(vcx, '<Import Project="$(VCTargetsPath)\\Microsoft.Cpp.targets" />',
          '<ItemGroup>\n    <ResourceCompile Include="app.rc" />\n  </ItemGroup>\n'
          '  <Import Project="$(VCTargetsPath)\\Microsoft.Cpp.targets" />', 1)

    # 4) Título da janela
    patch(proj / "DirectX.cpp", '#include "DirectX.h"', '#include "DirectX.h"\n#include "Branding.h"', 1)
    patch(proj / "DirectX.cpp",
          'sprintf_s(buf, ("KBotExt by kebs - %s %s \\t %s ###AnimatedTitle"), gamePatch.c_str(), connectedTo.c_str(), currentInfo.c_str());',
          'sprintf_s(buf, (APP_NAME " - %s %s \\t %s ###AnimatedTitle"), gamePatch.c_str(), connectedTo.c_str(), currentInfo.c_str());', 1)

    # 5) Checagem de atualização -> repositório próprio (ou desativada)
    patch(proj / "DirectX.cpp",
          "\tMisc::CheckVersion();\n\n\tif (S.checkPrerelease)\n\t\tMisc::CheckPrerelease(S.fileName);",
          "\tif (std::string(APP_GITHUB_REPO).size() > 0)\n\t{\n\t\tMisc::CheckVersion();\n\n"
          "\t\tif (S.checkPrerelease)\n\t\t\tMisc::CheckPrerelease(S.fileName);\n\t}", 1)
    misc = proj / "Misc.h"
    patch(misc, '#include "Config.h"', '#include "Config.h"\n#include "Branding.h"', 1)
    patch(misc, 'cpr::Url{ "https://api.github.com/repos/KebsCS/KBotExt/releases/latest" }',
          'cpr::Url{ "https://api.github.com/repos/" APP_GITHUB_REPO "/releases/latest" }', 1)
    patch(misc, 'cpr::Url{ "https://api.github.com/repos/KebsCS/KBotExt/releases/tags/prerelease" }',
          'cpr::Url{ "https://api.github.com/repos/" APP_GITHUB_REPO "/releases/tags/prerelease" }', 1)
    patch(misc, 'L"https://github.com/KebsCS/KBotExt/releases/latest"',
          'L"https://github.com/" APP_GITHUB_REPO_W L"/releases/latest"', 2)
    patch(misc, 'L"https://github.com/KebsCS/KBotExt/releases/tag/prerelease"',
          'L"https://github.com/" APP_GITHUB_REPO_W L"/releases/tag/prerelease"', 1)
    write(proj / "Branding.h", read(proj / "Branding.h") +
          '\n#define APP_WIDEN2(x) L##x\n#define APP_WIDEN(x) APP_WIDEN2(x)\n'
          '#define APP_GITHUB_REPO_W APP_WIDEN(APP_GITHUB_REPO)\n')

    # 6) Aba Settings: link do repositório + créditos
    st = proj / "SettingsTab.h"
    text = read(st)
    if '#include "Branding.h"' not in text:
        patch(st, "#pragma once", '#pragma once\n#include "Branding.h"', 1)
    patch(st,
          '\t\t\tImGui::Text("GitHub repository:");\n\t\t\tImGui::TextURL("Click me!", "https://github.com/KebsCS/KBotExt", 1, 0);\n'
          '\t\t\tImGui::SameLine();\n\t\t\tImGui::Text("| Discord server:");\n\t\t\tImGui::TextURL("Click me!", "https://discord.gg/qMmPBFpj2n", 1, 0);',
          '\t\t\tif (std::string(APP_GITHUB_REPO).size() > 0)\n\t\t\t{\n'
          '\t\t\t\tImGui::Text("GitHub repository:");\n'
          '\t\t\t\tImGui::TextURL("Click me!", "https://github.com/" APP_GITHUB_REPO, 1, 0);\n\t\t\t}\n'
          '\t\t\tImGui::TextWrapped(APP_ORIGINAL_CREDIT);', 1)

    # 7) Nome do lobby criado pelo app
    gt = proj / "GameTab.h"
    text = read(gt)
    if '#include "Branding.h"' not in text:
        patch(gt, "#pragma once", '#pragma once\n#include "Branding.h"', 1)
    patch(gt, '"lobbyName":"KBot"', '"lobbyName":")" APP_LOBBY_NAME R"("')

    # 8) Informações de versão do .exe (aparece em Propriedades e no Gerenciador de Tarefas)
    ver = re.search(r'programVersion = "([\d.]+)"', read(misc)).group(1)
    v = (ver.split(".") + ["0"] * 4)[:4]
    write(proj / "app.rc", f"""#include <winres.h>

VS_VERSION_INFO VERSIONINFO
 FILEVERSION {",".join(v)}
 PRODUCTVERSION {",".join(v)}
 FILEFLAGSMASK 0x3fL
 FILEFLAGS 0x0L
 FILEOS VOS_NT_WINDOWS32
 FILETYPE VFT_APP
 FILESUBTYPE 0x0L
BEGIN
    BLOCK "StringFileInfo"
    BEGIN
        BLOCK "041604b0"
        BEGIN
            VALUE "FileDescription", "{name}"
            VALUE "FileVersion", "{ver}"
            VALUE "InternalName", "{name}"
            VALUE "OriginalFilename", "{name}.exe"
            VALUE "ProductName", "{name}"
            VALUE "ProductVersion", "{ver}"
            VALUE "Comments", "Baseado no KBotExt de KebsCS - GPL-3.0"
        END
    END
    BLOCK "VarFileInfo"
    BEGIN
        VALUE "Translation", 0x416, 1200
    END
END
""")

    # 9) README
    readme = out / "README.md"
    write(readme, f"# {name}\n\n"
                  f"Versão renomeada do [KBotExt](https://github.com/KebsCS/KBotExt) de KebsCS, "
                  f"com a mesma funcionalidade. Licença original: GPL-3.0.\n\n---\n\n"
                  + read(readme).replace(f"{OLD}.sln", f"{name}.sln"))

    # 10) Workflow: só gera release se o build acontecer no próprio repositório
    wf = out / ".github" / "workflows" / "build.yml"
    if wf.exists():
        t = read(wf)
        t = t.replace("on:\n  push:\n    branches:\n      - main\n",
                      "on:\n  workflow_dispatch:\n  push:\n    branches:\n      - main\n      - master\n")
        t = re.sub(r'artifacts: "D:/a/[^"]*"', f'artifacts: "Release/{name}.exe"', t)
        t = t.replace("actions/upload-artifact@v3", "actions/upload-artifact@v4")
        t = t.replace("microsoft/setup-msbuild@v1.1", "microsoft/setup-msbuild@v2")
        write(wf, t)

    # Verificação final
    leftovers = []
    for f in out.rglob("*"):
        if f.is_file() and "imgui" not in f.parts and f.suffix in {".h", ".cpp", ".sln", ".vcxproj", ".filters", ".yml"}:
            for i, line in enumerate(read(f).splitlines(), 1):
                if re.search(r"kbot", line, re.I) and "KebsCS" not in line and "KBotExt de" not in line:
                    leftovers.append(f"{f.relative_to(out)}:{i}: {line.strip()}")
    print(f"Pronto: {out}")
    if leftovers:
        print("Ocorrências restantes do nome antigo:")
        print("\n".join(leftovers))


if __name__ == "__main__":
    main()
