# CRAB — Comprehensive RNA Analysis of Binding-motifs

CRAB is a web server for sequence- and structure-aware discovery of RNA-binding protein (RBP) binding motifs. RNA secondary structure is encoded with the BEAR alphabet. The motif collection is built on 1,244 CLIP datasets (POSTAR3 and GEO) covering 394 unique RBPs (422 species-specific entries) across seven model organisms. A Global Search mode provides consensus signatures that integrate all datasets available for each RBP, and CRAB-DB exposes them as a browsable catalogue.

**Web server:** https://crab.bio.uniroma2.it
**Motif database (versioned):** Zenodo DOI `[to be added]`

## Citation

Pepe G, Teofani A, Vanelli L, Valentini E, Ferrè F, Ausiello G, Helmer-Citterich M, Gherardini PF.
CRAB: integrative sequence and structure-aware motif discovery for RNA Binding Proteins across multiple model organisms. *Bioinformatics* (under review).

CRAB extends BRIO (Guarracino *et al.*, Nucleic Acids Res 2021, [doi:10.1093/nar/gkab400](https://doi.org/10.1093/nar/gkab400)).

## Repository layout

| Path | Content |
|---|---|
| `index.js`, `routes/`, `controllers/`, `views/` | Node.js/Express web application |
| `scripts/_completeWithDotBracketAndBEAR.py` | Main pipeline: folding (RNAfold), BEAR encoding, motif scan, Fisher's exact test |
| `scripts/search2.0.py` | Sliding-window ungapped PFM scan (MBR / nucleotide substitution matrices) |
| `scripts/output_generation.py` | Results dashboard generation |
| `scripts/BearEncoder_new.jar` | Dot-bracket → BEAR encoder |
| `resources/` | Substitution matrices (MBR), motif/domain dictionaries, precomputed background counts (`summary_AutoBg.txt`) |
| `public/brio-db/rbp_index.json` | CRAB-DB index |
| `examples/` | Example inputs |

## Data (Zenodo)

The following are too large for GitHub and are distributed as a versioned Zenodo record:

- `motifs_str_groups/`, `motifs_nuc_groups/`: structure and sequence motifs (per experiment and Global)
- `public/PFMs/`: position frequency matrices
- `public/images/logos/`: precomputed qBEAR / IUPAC logos
- `datasets.tsv`: accession-level provenance of all 1,244 datasets

Download and extract them into the repository root, keeping the paths above.

## Installation

```bash
conda env create -f environment.yml
conda activate crab
npm install
cp .env.example .env   # then edit
node index.js          # listens on port 3000
```

Software versions used in production: ViennaRNA 2.4.14, Python 3, SciPy, Node.js / Express 4.

## Versions

See [CHANGELOG.md](CHANGELOG.md) for database releases and update dates.

## License

See [LICENSE](LICENSE).
