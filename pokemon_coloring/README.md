# Pokémon para colorir (Geração 1)

Gera um PDF com uma página por Pokémon (#001 a #151) no estilo livro de colorir:
título com número e nome, o desenho grande em contorno para colorir e, embaixo,
a arte oficial colorida em tamanho pequeno como referência.

## Como funciona

A arte oficial de cada Pokémon é baixada do repositório público
[PokeAPI/sprites](https://github.com/PokeAPI/sprites) e convertida em contorno
("line art") por processamento de imagem:

- **Bordas internas:** diferença de gaussianas (DoG) sobre a versão em tons de cinza.
- **Contorno externo:** silhueta extraída do canal alpha (dilatação − erosão).
- **Limpeza:** remoção de manchas pretas isoladas (despeckle) por componentes conexas.

O resultado é montado em páginas A4 (150 DPI) e exportado como um único PDF.

## Uso

```bash
pip install pillow numpy scipy
python build.py
```

Saída: `Pokemon_150_para_colorir.pdf` e PNGs individuais em `pages/`.

## Arquivos

- `build.py` — pipeline completo (download → contorno → páginas → PDF).
- `lineart.py` — protótipo/uso isolado da conversão para contorno.

> Imagens © Nintendo/Game Freak. Uso pessoal/educacional.
