# Hugging Face: ordenamento padrão da aba Community

## Contexto
- Changelog do Hugging Face: donos de repositório podem definir o **ordenamento padrão** da aba **Community** (Discussions/PRs).
- Opções disponíveis: **Trending**, **Most Reactions** ou **Recently Created**.
- Changelog do Hugging Face (28/out/2025): donos de repositório podem definir o **ordenamento padrão** da aba **Community** (Discussions/PRs).
- Opções disponíveis: **Trending**, **Most Reactions** ou **Recently Created**.
- Evento notado no feed: a org **MatVerseHub** deu upvote no item "Set Default Sorting in the Community Tab" (66 upvotes).

## Impacto para MatVerseHub/MatVerseScan
- O ordenamento padrão direciona a atenção da comunidade e molda a experiência de auditoria pública.
- Perfis de uso:
  - **Trending**: prioriza threads com atividade recente/engajamento (atração de comunidade).
  - **Most Reactions**: prioriza sinal social (útil para priorização coletiva).
  - **Recently Created**: prioriza linha do tempo (útil para rastreabilidade/auditoria).

## Recomendação
Para quem usa a aba Community como trilha de auditoria (claims, issues de verificação, PRs de correção):
- Definir **Default = Recently Created**.
- Justificativa: minimiza ambiguidade temporal, reduz chance de perder itens novos e simplifica a revisão sequencial.

## Sugestão operacional
1. Abrir as **Settings** do repositório no Hugging Face (tab "Community").
2. Selecionar **Recently Created** como default.
3. Manter tópicos fixados relevantes (ex.: "How to verify PoSE/PoLE locally").
4. Usar labels/threads como **PoSE-Claim**, **PoLE-Execution**, **Snapshot**, **Consensus/Review** para log semântico humano.
