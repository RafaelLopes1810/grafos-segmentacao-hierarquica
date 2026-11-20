# Validação matemática da hierarquia

## Partições e fusões
Seja Ω o conjunto finito de N pixels RGB e P₀ a partição inicial em R regiões
não vazias. Cada passo substitui exatamente dois blocos disjuntos A e B pelo
bloco A∪B. Logo a cobertura de Ω e a disjunção são preservadas por indução,
|Pₜ| = R−t e Pₜ refina Pₜ₊₁. Nenhuma região fina pode atravessar dois blocos
de uma partição mais grossa. R−1 fusões produzem uma raiz e 2R−1 nós.
As médias usadas nas fusões devem ser ponderadas pelas áreas.

## Erro de reconstrução
Para cada bloco C, μ_C é a média RGB exata dos pixels originais.
SSE(P) = Σ_C Σ_{p∈C} ||x_p−μ_C||² e MSE(P) = SSE(P)/(3N),
conforme color_homogeneity_mse. Não usar cores uint8 arredondadas da visualização.

A identidade de decomposição da soma de quadrados fornece:
SSE(A∪B) − SSE(A) − SSE(B) =
(|A||B|/(|A|+|B|)) ||μ_A−μ_B||² ≥ 0.

Portanto MSE(Pₜ₊₁) ≥ MSE(Pₜ), independentemente da heurística que escolhe
a fusão. Há igualdade quando as médias coincidem. Isso não demonstra
otimalidade global da segmentação, nem garante monotonicidade se a imagem
ou a partição inicial for trocada. Suavização e espaço Lab orientam a
segmentação inicial; o MSE é medido no RGB original redimensionado.

## Cortes e alturas
O peso RGB recalculado pode diminuir após uma fusão. A implementação usa
h(v)=max(peso(v),h(filho esquerdo),h(filho direito)); assim h(pai)≥h(filho).
Isso é monotonicidade ao longo dos ramos, não necessariamente na lista
cronológica de fusões. Em um corte por limiar t, aceitar h(v)≤t implica
aceitar seus descendentes internos. Aumentar t produz partições aninhadas.
Empates são aceitos inclusivamente e podem remover várias regiões de uma vez.
Cortes por quantidade usam prefixos da lista e obtêm exatamente R−t regiões.

## Evidência automatizada
backend/tests/test_hierarchy_invariants.py percorre todas as contagens em
imagens pequenas determinísticas, verifica inclusão, cobertura, cardinalidade,
estrutura binária, alturas e a identidade de incremento de SSE. Também percorre
todos os limiares relevantes. Casos: pixel único, linha, coluna, cores constantes,
rótulos não consecutivos e imagens pseudoaleatórias com sementes fixas.

Executar na raiz: PYTHONPATH=backend python -m pytest backend/tests -q
No PowerShell: $env:PYTHONPATH="backend"; python -m pytest backend/tests -q
