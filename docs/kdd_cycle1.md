# Ciclo 1 do KDD: o enquadramento inicial e por que ele mudou

Este documento registra o primeiro ciclo do processo KDD do trabalho. Serve de base para a seção de ciclos e lições aprendidas do artigo. O código desse ciclo foi aposentado; o que continua relevante para a pergunta atual (duplicatas, artefato do arquivamento, estado das tarefas) é recalculado em [`notebooks/01_data_understanding.ipynb`](../notebooks/01_data_understanding.ipynb).

**Dados usados no ciclo 1:** amostra oficial de 500 repositórios do SpecMine v1.0 (commit `da606c8` de `shyamagarwal13/specmine-official`) e 13 colunas de `spec_files` do censo amplo completo (mirror no Hugging Face), com a mesma janela de observação (commits até 2026-07-11).

## Enquadramento inicial

**Pergunta original:** muitas specs do SpecMine têm um único commit. Elas são artefatos concluídos e estáveis, ou processos de especificação interrompidos?

Três dimensões, medidas como indicadores (não como prova de abandono):

| Dimensão | Indicador usado no ciclo 1 |
|---|---|
| Potencial desatualização | A spec parou de receber commits enquanto o repositório continuou ativo (`repo_pushed_at` ou outras specs editadas depois) |
| Potencial trabalho inacabado | Tarefas OpenSpec pendentes; PRs de spec não integrados |
| Potencial interrupção | O repositório recebeu pushes ≥ T dias depois do último commit de spec |

## O que encontramos

| # | Achado | Números |
|---|---|---|
| 1 | **O "commit único" é sobretudo um artefato de medição.** O histórico é contado por caminho e não acompanha a renomeação da pasta para `archive/` no OpenSpec. | 81,7% das specs da amostra têm um único commit. Specs arquivadas são 50,6% da amostra e 96,6% delas têm commit único; em 86% o primeiro commit está a até 2 dias da data de arquivamento no caminho. Sem as arquivadas, a taxa cai para 66,4%. |
| 2 | **Specs vivas evoluem por arquivamento de mudanças.** | 78% dos commits em specs vivas do OpenSpec coincidem com um commit de arquivamento. |
| 3 | **A evolução é em rajadas.** | Intervalo mediano entre commits de 1,8 dia; 43% no mesmo dia. Kaplan–Meier: 44% das specs vivas sem 2º commit em 90 dias. |
| 4 | **O indicador de desatualização mede tamanho do repositório.** Com mais specs, é quase certo que *alguma* outra foi editada depois. | Desatualização (T = 30 dias) no censo: 21% em repos com 1 spec, 34% com 2–5, 40% com 6–20, 50% com 21–100, 73% com mais de 100. Specs vivas: 86% na amostra contra 50% no censo. |
| 5 | **Interrupção é dominada pela amostra e pela dormência total.** | Repositórios sinalizados (T = 30): 67,8% na amostra contra 23,2% no censo. No censo, em 48,5% dos repositórios em risco o último push ocorre a menos de 1 dia da última spec: o repositório inteiro parou. Nenhum dos 14 repositórios com mais de uma ferramenta mostra troca sequencial de ferramenta. |
| 6 | **PRs não integrados não são mensuráveis.** A camada de PRs é descoberta a partir de commits já integrados. | 5.322 de 5.322 PRs estão fechados e integrados. |
| 7 | **A amostra não representa a população.** | Repositórios com ≥ 100 estrelas: 61,2% na amostra contra 1,3% no censo. Repositórios com uma única spec: 29,9% contra 71,3%. |
| 8 | **Trabalho inacabado tem sinal limpo e mensurável.** O próprio OpenSpec registra o fim de uma mudança (arquivamento e checkboxes). | Na amostra, 60,6% das mudanças ativas com tarefas têm pendências e 15,6% das arquivadas foram fechadas com itens desmarcados. |

## Decisão: realinhamento para o ciclo 2

- **Desatualização** ficou inconclusiva: o indicador é confundido pelo tamanho do repositório, e o SpecMine não tem os commits de código dos repositórios para verificar se a spec ficou para trás em relação ao código.
- **Interrupção** reflete principalmente a dormência do repositório inteiro e o viés da amostra.
- **Trabalho inacabado** é a única dimensão com sinal limpo e com um marcador explícito de conclusão nos dados.

**Nova pergunta de pesquisa:** com que frequência mudanças de especificação OpenSpec ficam inacabadas, e o que as distingue das concluídas?

**Consequências para o desenho:**

- A unidade de análise passa a ser a **mudança** (`openspec/changes/<nome>/`), não o arquivo de spec (achados 1 e 2).
- As estimativas devem vir do censo completo, não da amostra (achado 7).
- A mineração usa atributos de conteúdo, porque os atributos de tempo das mudanças arquivadas se perderam na renomeação (achado 1).

## Lições aprendidas

1. **Entender como o dado foi coletado antes de minerar.** O padrão mais forte do ciclo 1 (specs que "nascem arquivadas") era um efeito da coleta, não do comportamento dos desenvolvedores.
2. **Indicadores relativos precisam de controle de escala.** Um sinal que cresce com o tamanho do repositório parece um fenômeno, mas é composição.
3. **Amostras curadas inflam taxas.** Prevalências precisam vir da população.
4. **Preferir processos que registram o próprio fim.** Medir "inacabado" só é possível porque o OpenSpec marca a conclusão de forma explícita.
