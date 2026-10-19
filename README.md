# SSA notebooks

Jupyter notebooks on space situational awareness and satellite tracking. Rendered output: https://jazzpi.github.io/ssa/

## Workflow

```sh
nix develop
jupyter lab
```

Create notebooks under `notebooks/`. `jupytext.toml` pairs every notebook with a `.py` (percent format); JupyterLab and Jupyter Notebook keep both in sync on save. Only the `.py` files are tracked — `.ipynb` files are gitignored. If you edit a `.py` or `.ipynb` outside those UIs, run `jupytext --sync notebooks/*.py`.

### VS Code

VS Code's built-in notebook editor does **not** sync the `.py`. Either edit the `.py` directly (`# %%` cells run via the Jupyter extension), or install the recommended "Jupytext for VS Code" extension, which opens the `.py` as a notebook and saves back to it. It needs `jupytext` on `PATH`, so launch VS Code from `nix develop`.

Notebooks must not fetch data at run time: embed TLEs etc. so CI can execute them reproducibly.

## Publishing

Pushes to `main` run `.github/workflows/pages.yml`, which executes all notebooks (`scripts/build-site.sh`) and deploys the HTML to GitHub Pages. One-time setup: repo Settings → Pages → Source: "GitHub Actions".

To build locally: `nix develop -c ./scripts/build-site.sh` (output in `_site/`).
