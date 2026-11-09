#pragma once

// ===== Identidade do aplicativo =====
// Edite aqui para mudar o nome que aparece na janela, no lobby, etc.
#define APP_NAME        "NexusKit"
#define APP_NAME_W      L"NexusKit"

// Repositório GitHub usado para avisar de novas versões ("usuario/repo").
// Deixe vazio ("") para desativar a checagem de atualização.
#define APP_GITHUB_REPO ""

// Nome usado ao criar lobbies personalizados / Practice Tool
#define APP_LOBBY_NAME  "NexusKit"

// Créditos do projeto original (licença GPL-3.0 exige manter o aviso)
#define APP_ORIGINAL_CREDIT "Baseado no KBotExt de KebsCS (github.com/KebsCS/KBotExt) - GPL-3.0"

#define APP_WIDEN2(x) L##x
#define APP_WIDEN(x) APP_WIDEN2(x)
#define APP_GITHUB_REPO_W APP_WIDEN(APP_GITHUB_REPO)
