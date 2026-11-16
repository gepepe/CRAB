import json
import os
import my_email
import shutil


def generate_output(dir_base, path_complete_input_rna_molecules,
                    path_results_html, path_tab_sequences_txt, path_tab_enriched_motifs_txt,
                    dir_user_download,
                    sequence_results_dict, motif_results_dict, seq_to_sign_motifs_dict,
                    user_email, species_to_protein_to_link_dict,species_to_protein_to_entry_name,
                    reproduciblePeakFilename_to_RBP_CellLine_dict, publication_to_Link_dict):

    # Raccogliamo (coverage, p-value) di tutti i motivi esportabili (p<0.05, coverage>=0.1).
    # Serve sia per capire se la tabella e' vuota, sia per scegliere i filtri iniziali.
    motif_stats = []
    for str_or_nuc in sequence_results_dict:
        for motif in motif_results_dict.get(str_or_nuc, {}):
            try:
                p_value = float("%.2g" % motif_results_dict[str_or_nuc][motif][2])
                if p_value >= 0.05:
                    continue

                coverage = float("%.2g" % motif_results_dict[str_or_nuc][motif][0])
                if coverage < 0.1:  # Esportiamo fino al 10%, il JS filtrera'
                    continue

                motif_stats.append((coverage, p_value))
            except (KeyError, IndexError, ValueError):
                continue

    table_empty = (len(motif_stats) == 0)

    # Scelta dei filtri iniziali: i piu' stringenti che mostrano ancora almeno un risultato.
    # Cascata richiesta: prima si abbassa la coverage (1.0 -> 0.75 -> 0.5) tenendo p-value < 0.001,
    # poi si allenta il p-value (0.01 -> 0.05). Reti di sicurezza finali per non mostrare una
    # pagina vuota se i risultati esistono solo sotto coverage 0.5.
    initial_cov = 0.50
    initial_pval = 0.05
    if not table_empty:
        filter_cascade = [
            (1.00, 0.001),
            (0.75, 0.001),
            (0.50, 0.001),
            (0.50, 0.01),
            (0.50, 0.05),
            (0.25, 0.05),
            (0.10, 0.05),
        ]
        initial_cov, initial_pval = 0.10, 0.05  # fallback estremo: mostra tutto l'esportato
        for cov_cut, pval_cut in filter_cascade:
            if any(cov >= cov_cut and pval <= pval_cut for (cov, pval) in motif_stats):
                initial_cov, initial_pval = cov_cut, pval_cut
                break

    user = dir_user_download.split("/")[-2]
    if not os.path.exists(dir_user_download + "/logos"):
        os.makedirs(dir_user_download + "/logos")

    total_file_dict = {}
    if os.path.exists(dir_user_download + "/motifs/"):
        files = os.listdir(dir_user_download + "/motifs/")
        for file in files:
            try:
                opened_file = open(dir_user_download + "/motifs/" + file).readlines()
                for line in opened_file[1:]:
                    split_line = line.split("\t")
                    if file not in total_file_dict:
                        total_file_dict[file] = {}
                    total_file_dict[file][split_line[0]] = split_line[1:]
            except Exception:
                continue

    len_dict = {}
    count_len = 0
    input_file = open(path_complete_input_rna_molecules, 'r')
    line = input_file.readline()
    while(line):
        if line.startswith(">"):
            nome = line[1:-1].strip()
            line = input_file.readline()
            len_dict[nome] = len(line.strip())
            if len(line.strip()) < 50:
                count_len += 1
        line = input_file.readline()
    input_file.close()

    with open(path_results_html, 'w') as fw:

        # STILE CSS
        fw.write("<style>\n")
        fw.write("  .container, .container-fluid { max-width: 96% !important; width: 96% !important; }\n")
        fw.write("  .custom-tab-panel { display: none !important; }\n")
        fw.write("  .custom-tab-panel.active { display: block !important; }\n")
        fw.write("  .nav-pills .nav-link { border-radius: 20px; text-transform: uppercase; font-size: 12px; letter-spacing: 0.5px; }\n")
        fw.write("  .nav-pills .nav-link.active { background-color: #4f46e5 !important; color: white !important; box-shadow: 0 4px 6px -1px rgba(79, 70, 229, 0.2); }\n")
        fw.write("  #enrichedTable th, #enrichedTable td, #sequencesTable th, #sequencesTable td {\n")
        fw.write("      white-space: normal !important; word-break: break-word !important;\n")
        fw.write("      padding: 8px 6px !important; vertical-align: middle !important; font-size: 13px !important;\n")
        fw.write("  }\n")
        fw.write("  .badge-sequence { background-color: #e6fbf3 !important; color: #10b981 !important; border: 1px solid #a7f3d0 !important; font-weight: bold; }\n")
        fw.write("  .badge-structure { background-color: #fff1f2 !important; color: #f43f5e !important; border: 1px solid #fecaca !important; font-weight: bold; }\n")
        fw.write("  td.details-control { text-align: center; cursor: pointer; color: #4f46e5; vertical-align: middle !important; width: 40px; }\n")
        fw.write("  td.details-control i { transition: transform 0.2s ease-in-out; }\n")
        fw.write("  tr.shown td.details-control i { transform: rotate(45deg); color: #f43f5e; }\n")
        # Logo cliccabile + lightbox
        fw.write("  img.logo-zoomable { cursor: zoom-in; transition: transform 0.15s ease, box-shadow 0.15s ease; }\n")
        fw.write("  img.logo-zoomable:hover { transform: scale(1.08); box-shadow: 0 4px 12px rgba(0,0,0,0.18); }\n")
        fw.write("  .logo-lightbox-overlay { display: none; position: fixed; top: 0; left: 0; right: 0; bottom: 0; z-index: 20000; background: rgba(15, 23, 42, 0.82); align-items: center; justify-content: center; padding: 4vh 4vw; cursor: zoom-out; }\n")
        fw.write("  .logo-lightbox-overlay.open { display: flex; }\n")
        fw.write("  .logo-lightbox-overlay img { max-width: 92vw; max-height: 80vh; background: #fff; padding: 18px; border-radius: 10px; box-shadow: 0 20px 50px rgba(0,0,0,0.45); cursor: default; }\n")
        fw.write("  .logo-lightbox-close { position: absolute; top: 16px; right: 26px; color: #fff; font-size: 34px; line-height: 1; cursor: pointer; opacity: 0.85; font-weight: 300; }\n")
        fw.write("  .logo-lightbox-close:hover { opacity: 1; }\n")
        fw.write("  .logo-lightbox-caption { position: absolute; bottom: 20px; left: 0; right: 0; text-align: center; color: #e2e8f0; font-size: 13px; padding: 0 20px; }\n")
        fw.write("  .child-table-wrapper { padding: 12px; background-color: #f8fafc; border-bottom: 1px solid #e2e8f0; }\n")
        # Stile aggiuntivo per lo slider
        fw.write("  .custom-range::-webkit-slider-thumb { background: #4f46e5; }\n")
        fw.write("  .custom-range::-moz-range-thumb { background: #4f46e5; }\n")
        fw.write("  .custom-range::-ms-thumb { background: #4f46e5; }\n")
        fw.write("</style>\n")

        # Intestazione della pagina
        fw.write("<div class='container-fluid my-4'>\n")
        fw.write("  <div class='card shadow-sm mb-4' style='border-radius: 12px; overflow: hidden;'>\n")
        
        # ROW 1: Titolo e Pulsanti di Azione
        fw.write("    <div class='card-body d-flex justify-content-between align-items-center flex-wrap pb-3'>\n")
        fw.write("      <div>\n")
        fw.write("        <h4 class='mb-1 font-weight-bold text-dark' style='letter-spacing:-0.5px;'>BRIO Analysis Results</h4>\n")
        fw.write("        <p class='text-muted small mb-0'>Explore enriched RNA sequence and secondary structure motifs.</p>\n")
        fw.write("      </div>\n")
        fw.write("      <div class='d-flex gap-2 align-items-center'>\n")
        fw.write("        <button class='btn btn-info btn-sm mr-2 font-weight-bold shadow-sm text-white' style='border-radius:6px;' type='button' data-toggle='collapse' data-target='#collapseExample' aria-expanded='false'><i class='fa fa-map mr-1'></i> Show qBEAR Legend</button>\n")
        fw.write(f"        <a href='results/{user}/complete_input_with_dot_bracket_and_bear.txt' download class='btn btn-outline-secondary btn-sm mr-2' style='border-radius:6px;'><i class='fa fa-download'></i> Download Input</a>\n")
        fw.write(f"        <a href='results/{user}/download.zip' download class='btn btn-primary btn-sm font-weight-bold shadow-sm' style='border-radius:6px; background-color:#4f46e5; border-color:#4f46e5;'><i class='fa fa-file-archive'></i> Download All (ZIP)</a>\n")
        fw.write("      </div>\n")
        fw.write("    </div>\n")
        
        # ROW 2: Barra dei Filtri Dedicata (Slider e Select)
        fw.write("    <div class='bg-light border-top px-4 py-3 d-flex align-items-center flex-wrap' style='gap: 40px;'>\n")
        # Filtro P-Value
        fw.write("      <div class='d-flex align-items-center'>\n")
        fw.write("        <label class='font-weight-bold small mb-0 mr-2 text-secondary'><i class='fa fa-filter mr-1'></i> Max FDR p-value:</label>\n")
        fw.write("        <select class='custom-select custom-select-sm shadow-sm border-0' id='pvalueFilterSelect' onchange='applyFilters()' style='width: 100px; border-radius: 6px;'>\n")
        _sel_p05 = " selected" if abs(initial_pval - 0.05) < 1e-9 else ""
        _sel_p01 = " selected" if abs(initial_pval - 0.01) < 1e-9 else ""
        _sel_p001 = " selected" if abs(initial_pval - 0.001) < 1e-9 else ""
        fw.write(f"          <option value='0.05'{_sel_p05}>&lt; 0.05</option>\n")
        fw.write(f"          <option value='0.01'{_sel_p01}>&lt; 0.01</option>\n")
        fw.write(f"          <option value='0.001'{_sel_p001}>&lt; 0.001</option>\n")
        fw.write("        </select>\n")
        fw.write("      </div>\n")
        # Filtro Coverage con Slider
        fw.write("      <div class='d-flex align-items-center flex-grow-1' style='max-width: 400px;'>\n")
        fw.write(f"        <label class='font-weight-bold small mb-0 mr-3 text-secondary' style='min-width: 130px;'><i class='fa fa-sliders-h mr-1'></i> Min Coverage: <span id='covLabel' class='badge badge-primary px-2 py-1 ml-1'>&gt; {int(round(initial_cov * 100))}%</span></label>\n")
        fw.write("        <div class='w-100 position-relative pb-3'>\n")
        fw.write(f"          <input type='range' class='custom-range w-100' id='coverageFilterSelect' min='0.10' max='1.00' step='0.05' value='{initial_cov:.2f}' oninput='updateCoverageLabel(this.value)' onchange='applyFilters()'>\n")
        fw.write("          <div class='d-flex justify-content-between w-100 mt-1 position-absolute text-muted' style='font-size: 10px; bottom: 0px; pointer-events: none;'>\n")
        fw.write("            <span>Permissive (10%)</span>\n")
        fw.write("            <span>Stringent (100%)</span>\n")
        fw.write("          </div>\n")
        fw.write("        </div>\n")
        fw.write("      </div>\n")
        fw.write("    </div>\n")

        fw.write("    <div class='collapse' id='collapseExample'>\n")
        fw.write("      <div class='card-footer bg-white border-top p-4 legenda-container'>\n")
        fw.write("        <h6 class='font-weight-bold text-secondary mb-3 text-center'><i class='fa fa-info-circle mr-1'></i> qBEAR Structural Alphabet Legend</h6>\n")
        fw.write("        <img src='../../images/bear.png' id='qbear_legend' class='img-fluid shadow-sm border rounded bg-white p-2'>\n")
        fw.write("      </div>\n")
        fw.write("    </div>\n")
        fw.write("  </div>\n")

        try:
            shutil.copyfile(path_complete_input_rna_molecules, os.path.join(dir_user_download, 'input.txt'))
        except Exception:
            pass

        if not table_empty:
            tab1 = open(path_tab_enriched_motifs_txt, "w")
            tab2 = open(path_tab_sequences_txt, "w")
            tab2.write("Name\tMotif_ID\tStart\tEnd\tEnriched Motif\tType\tProtein\tExperiment\n")

            if count_len > 0:
                fw.write(f"<div class='alert alert-warning shadow-sm mb-4'><i class='fa fa-exclamation-triangle mr-2'></i> <strong>{count_len}</strong> sequence(s) shorter than 50 nucleotides were not scanned for structure motifs.</div>\n")

            fw.write("<ul class='nav nav-pills mb-4' id='resultsTabs'>\n")
            fw.write("  <li class='nav-item'><button class='nav-link active font-weight-bold px-4 btn btn-link' id='btn-charts' onclick='switchTab(\"chartsPanel\", \"btn-charts\")'><i class='fa fa-chart-line mr-1'></i> Motif Mapping</button></li>\n")
            fw.write("  <li class='nav-item'><button class='nav-link font-weight-bold px-4 btn btn-link text-secondary' id='btn-enriched' onclick='switchTab(\"enrichedPanel\", \"btn-enriched\")'>Enriched Motifs</button></li>\n")
            fw.write("  <li class='nav-item'><button class='nav-link font-weight-bold px-4 btn btn-link text-secondary' id='btn-sequences' onclick='switchTab(\"sequencesPanel\", \"btn-sequences\")'>Sequences Match</button></li>\n")
            fw.write("</ul>\n")

            fw.write("<div id='logoLightbox' class='logo-lightbox-overlay'>\n")
            fw.write("  <span class='logo-lightbox-close' title='Close'>&times;</span>\n")
            fw.write("  <img id='logoLightboxImg' src='' alt='Motif logo enlarged'>\n")
            fw.write("  <div id='logoLightboxCaption' class='logo-lightbox-caption'></div>\n")
            fw.write("</div>\n")

            fw.write("<div id='resultsTabsContent'>\n")

            # =========================================================
            # TABELLA 1: ENRICHED MOTIFS PANEL
            # =========================================================
            fw.write("  <div class='custom-tab-panel' id='enrichedPanel'>\n")
            fw.write("    <div class='card shadow-sm' style='border-radius: 12px;'>\n")
            fw.write("      <div class='card-body p-3'>\n")
            fw.write("        <div class='table-responsive'>\n")
            fw.write("          <table id='enrichedTable' class='table table-hover table-striped border mb-0' style='width:100%'>\n")
            fw.write("            <thead class='thead-light'>\n")
            fw.write("              <tr>\n")
            fw.write("                <th>Logo</th>\n")
            fw.write("                <th>Type</th>\n")
            fw.write("                <th>Region</th>\n")
            fw.write("                <th>Coverage</th>\n")
            fw.write("                <th>FDR</th>\n")
            fw.write("                <th>Experiment</th>\n")
            fw.write("                <th>UniprotKB ID</th>\n")
            fw.write("                <th>Domains</th>\n")
            fw.write("                <th>Cell line</th>\n")
            fw.write("                <th>Info</th>\n")
            fw.write("                <th>Organism</th>\n")
            fw.write("                <th>Download</th>\n")
            fw.write("              </tr>\n")
            fw.write("            </thead>\n")
            fw.write("            <tbody>\n")

            tab1.write("Motif_ID\tType\tRegion\tCoverage\tp-value\tExperiment\tUniprotKB_ID\tDomains\tCell_lines\tExperiment_Info\tOrganism\n")

            grouped_motifs = {}
            for str_or_nuc in sequence_results_dict:
                for motif in motif_results_dict.get(str_or_nuc, {}):
                    try:
                        p_value_float = float("%.2g" % motif_results_dict[str_or_nuc][motif][2])
                        coverage_float = float("%.2g" % motif_results_dict[str_or_nuc][motif][0])
                        if p_value_float >= 0.05 or coverage_float < 0.1:
                            continue

                        group_key = (motif, str_or_nuc)
                        region = motif.split("_")[-3] if len(motif.split("_")) >= 3 else "unknown"
                        experiment = "eCLIP" if motif.startswith("ENC") else motif.split("_")[0]
                        protein = motif.split("_")[1] if len(motif.split("_")) >= 2 else "unknown"
                        domains = "; ".join(motif_results_dict[str_or_nuc][motif][3]) if motif_results_dict[str_or_nuc][motif][3] else "-"

                        organism_names = {
                            'hg19': 'Homo sapiens', 'hg38': 'Homo sapiens', 'mm9': 'Mus musculus', 'mm10': 'Mus musculus', 'GRCm39': 'Mus musculus',
                            'dm6': 'Drosophila melanogaster', 'zv9': 'Danio rerio', 'dr10': 'Danio rerio', 'danRer11': 'Danio rerio',
                            'ce11': 'Caenorhabditis elegans', 'sacCer3': 'Saccharomyces cerevisiae', 'tair10': 'Arabidopsis thaliana'
                        }
                        organism = next((name for genome, name in organism_names.items() if f"_{genome}_" in motif), "Unknown")
                        species = next((genome for genome in organism_names.keys() if f"_{genome}_" in motif), None)

                        cell_lines = "-"
                        info = "-"
                        if experiment == "eCLIP":
                            if motif.split("_")[0] in reproduciblePeakFilename_to_RBP_CellLine_dict:
                                cell_lines = reproduciblePeakFilename_to_RBP_CellLine_dict[motif.split("_")[0]][1]
                                info = "https://www.encodeproject.org/search/?searchTerm=" + motif.split("_")[0]
                        else:
                            if len(motif.split("_")) >= 3 and motif.split("_")[2] in publication_to_Link_dict:
                                info = publication_to_Link_dict[motif.split("_")[2]]

                        if group_key not in grouped_motifs:
                            grouped_motifs[group_key] = {
                                'str_or_nuc': str_or_nuc, 'p_value': p_value_float, 'coverage': coverage_float,
                                'regions': {region}, 'experiment': experiment, 'protein': protein, 'domains': domains,
                                'cell_lines': cell_lines, 'info': info, 'organism': organism, 'species': species
                            }
                        else:
                            grouped_motifs[group_key]['regions'].add(region)
                            if p_value_float < grouped_motifs[group_key]['p_value']:
                                grouped_motifs[group_key]['p_value'] = p_value_float
                            if coverage_float > grouped_motifs[group_key]['coverage']:
                                grouped_motifs[group_key]['coverage'] = coverage_float
                    except Exception:
                        continue

            for (motif, str_or_nuc), data in grouped_motifs.items():
                tipo = "Structure" if str_or_nuc == "str" else "Sequence"
                p_value_str = str("%.2g" % data['p_value'])
                coverage_str = str("%.2g" % data['coverage'])
                regions_str = ", ".join(sorted(list(data['regions'])))

                if str_or_nuc == "nuc":
                    path_logo_on_server = os.path.join(dir_base, 'public/images/logos', motif.split(".")[0] + "_wl.nuc.png")
                    logo_link = "../images/logos/" + motif.split(".")[0] + "_wl.nuc.png"
                    path_pfm_on_server = os.path.join(dir_base, 'public/PFMs', motif.split(".")[0] + "_wl.nuc.pfm.csv")
                else:
                    path_logo_on_server = os.path.join(dir_base, 'public/images/logos', motif.split(".")[0] + "_wl.png")
                    logo_link = "../images/logos/" + motif.split(".")[0] + "_wl.png"
                    path_pfm_on_server = os.path.join(dir_base, 'public/PFMs', motif.split(".")[0] + "_wl.pfm.csv")

                try:
                    os.system(f"cp {path_logo_on_server} {dir_user_download}/logos/")
                    os.system(f"cp {path_pfm_on_server} {dir_user_download}/logos/")
                except Exception:
                    pass

                tab1.write(f"{motif[:-4]}\t{tipo}\t{regions_str}\t{coverage_str}\t{p_value_str}\t{data['experiment']}\t{data['protein']}\t{data['domains']}\t{data['cell_lines']}\t{data['info']}\t{data['organism']}\n")

                type_badge = "<span class='badge badge-sequence px-2 py-1'>Sequence</span>" if tipo == "Sequence" else "<span class='badge badge-structure px-2 py-1'>Structure</span>"
                exp_badge = f"<span class='badge badge-light border text-secondary'>{data['experiment']}</span>"

                fw.write(f"            <tr data-pvalue='{data['p_value']}' data-coverage='{data['coverage']}'>\n")
                logo_caption = f"{motif[:-4]} - {data['protein']} ({tipo})".replace("'", "")
                fw.write(f"              <td><img src='{logo_link}' class='logo-zoomable' data-caption='{logo_caption}' style='max-height:42px; max-width:160px; border-radius:4px;'></td>\n")
                fw.write(f"              <td>{type_badge}</td>\n")
                fw.write(f"              <td><span class='text-dark font-weight-bold small'>{regions_str}</span></td>\n")
                fw.write(f"              <td>{coverage_str}</td>\n")
                fw.write(f"              <td><span class='text-muted small'>{p_value_str}</span></td>\n")
                fw.write(f"              <td>{exp_badge}</td>\n")

                if data['species'] and data['protein'] in species_to_protein_to_link_dict.get(data['species'], {}) and species_to_protein_to_link_dict[data['species']][data['protein']]:
                    p_name = species_to_protein_to_entry_name[data['species']][data['protein']]
                    fw.write(f"              <td><a href='{species_to_protein_to_link_dict[data['species']][data['protein']]}' target='_blank' class='font-weight-bold'><i class='fa fa-external-link-alt mr-1 small'></i>{p_name}</a></td>\n")
                else:
                    fw.write(f"              <td><span class='text-dark font-weight-bold'>{data['protein']}</span></td>\n")

                fw.write(f"              <td><span class='small text-muted'>{data['domains']}</span></td>\n")
                fw.write(f"              <td>{data['cell_lines']}</td>\n")
                fw.write(f"              <td><a href='{data['info']}' target='_blank' class='btn btn-xs btn-outline-primary py-0 px-2 small font-weight-bold'>Link</a></td>\n" if data['info'] and data['info'] != "-" else "              <td>-</td>\n")
                fw.write(f"              <td><span class='font-italic small text-secondary'>{data['organism']}</span></td>\n")
                fw.write(f"              <td><a href='results/{user}/download/motifs/{motif}' download class='btn btn-light btn-sm text-primary py-1 px-2 border'><i class='fa fa-download'></i></a></td>\n")
                fw.write("            </tr>\n")

            fw.write("            </tbody>\n")
            fw.write("          </table>\n")
            fw.write("        </div>\n")
            fw.write("      </div>\n")
            fw.write("    </div>\n")
            fw.write("  </div>\n")

            # =========================================================
            # TABELLA 2: SEQUENCES MATCH PANEL (Child Rows API)
            # =========================================================
            fw.write("  <div class='custom-tab-panel' id='sequencesPanel'>\n")
            fw.write("    <div class='card shadow-sm' style='border-radius: 12px;'>\n")
            fw.write("      <div class='card-body p-3'>\n")
            fw.write("        <div class='table-responsive'>\n")
            fw.write("          <table id='sequencesTable' class='table table-hover border mb-0' style='width:100%'>\n")
            fw.write("            <thead class='thead-light'>\n")
            fw.write("              <tr>\n")
            fw.write("                <th></th>\n")
            fw.write("                <th>RNA Molecule ID</th>\n")
            fw.write("                <th>Total Binding Sites</th>\n")
            fw.write("              </tr>\n")
            fw.write("            </thead>\n")
            fw.write("            <tbody>\n")

            child_tables_dict = {}

            for single_input in seq_to_sign_motifs_dict:
                sequence_species = None
                for m in seq_to_sign_motifs_dict[single_input]:
                    for genome in ['hg19', 'hg38', 'mm9', 'mm10', 'GRCm39', 'dm6', 'zv9', 'dr10', 'danRer11', 'ce11', 'sacCer3', 'tair10']:
                        if f"_{genome}_" in m:
                            sequence_species = genome
                            break
                    if sequence_species: break

                sub_rows_html = ""
                count_sites = 0

                for m in seq_to_sign_motifs_dict[single_input]:
                    try:
                        start = str(total_file_dict[m][single_input][3])
                        end = str(total_file_dict[m][single_input][4])
                        motif_string = total_file_dict[m][single_input][0]
                        protein = m.split("_")[1]
                        
                        if m in motif_results_dict.get('nuc', {}): motif_type = "Sequence"
                        elif m in motif_results_dict.get('str', {}): motif_type = "Structure"
                        else:
                            motif_type = "Structure"
                            for k in motif_results_dict.get('nuc', {}):
                                if k.split('.')[0] == m.split('.')[0]:
                                    motif_type = "Sequence"
                                    break

                        experiment = "eCLIP" if m.startswith("ENC") else m.split("_")[0]
                        
                        str_or_nuc_key = 'nuc' if motif_type == "Sequence" else 'str'
                        target_dict = motif_results_dict.get(str_or_nuc_key, {})
                        orig_pvalue = 0.04
                        orig_coverage = 0.6 
                        if m in target_dict:
                            orig_pvalue = float("%.2g" % target_dict[m][2])
                            orig_coverage = float("%.2g" % target_dict[m][0])
                        else:
                            for k in target_dict:
                                if k in m or m in k or k.split('.')[0] == m.split('.')[0]:
                                    orig_pvalue = float("%.2g" % target_dict[k][2])
                                    orig_coverage = float("%.2g" % target_dict[k][0])
                                    break

                        tab2.write(f"{single_input}\t{m[:-4]}\t{start}\t{end}\t{motif_string}\t{motif_type}\t{protein}\t{experiment}\n")

                        type_badge = "<span class='badge badge-sequence px-2 py-1'>Sequence</span>" if motif_type == "Sequence" else "<span class='badge badge-structure px-2 py-1'>Structure</span>"
                        exp_badge = f"<span class='badge badge-light border text-secondary'>{experiment}</span>"

                        if sequence_species and protein in species_to_protein_to_link_dict.get(sequence_species, {}) and species_to_protein_to_link_dict[sequence_species][protein]:
                            protein_display_name = species_to_protein_to_entry_name[sequence_species][protein]
                            prot_html = f"<a href='{species_to_protein_to_link_dict[sequence_species][protein]}' target='_blank' class='font-weight-bold'><i class='fa fa-external-link-alt mr-1 small'></i>{protein_display_name}</a>"
                        else:
                            prot_html = f"<span class='text-dark font-weight-bold'>{protein}</span>"

                        sub_rows_html += f"<tr class='child-motif-row' data-pvalue='{orig_pvalue}' data-coverage='{orig_coverage}' data-start='{start}' data-end='{end}' data-protein='{protein}' data-type='{motif_type}'><td><span class='badge badge-dark font-weight-normal'>{start}</span></td><td><span class='badge badge-dark font-weight-normal'>{end}</span></td><td><code class='text-dark font-weight-bold'>{motif_string}</code></td><td>{type_badge}</td><td>{prot_html}</td><td>{exp_badge}</td></tr>"
                        count_sites += 1
                    except Exception:
                        continue
                
                if count_sites > 0:
                    full_child_table = f"<div class='child-table-wrapper'><table class='table table-sm border bg-white mb-0'><thead><tr class='text-secondary small text-uppercase bg-light'><th>Start</th><th>End</th><th>Identified Motif</th><th>Type</th><th>Protein</th><th>Experiment</th></tr></thead><tbody>{sub_rows_html}</tbody></table></div>"
                    child_tables_dict[single_input] = full_child_table

                    fw.write(f"            <tr>\n")
                    fw.write(f"              <td class='details-control' data-rna='{single_input}'><i class='fa fa-plus-circle fa-lg'></i></td>\n")
                    fw.write(f"              <td class='font-weight-bold text-dark'>{single_input}</td>\n")
                    fw.write(f"              <td><span class='badge badge-secondary'>{count_sites} bindings (varies with filters)</span></td>\n")
                    fw.write(f"            </tr>\n")

            fw.write("            </tbody>\n")
            fw.write("          </table>\n")
            fw.write("        </div>\n")
            fw.write("      </div>\n")
            fw.write("    </div>\n")
            fw.write("  </div>\n")

            # =========================================================
            # TABELLA 3: MOTIF MAPPING 
            # =========================================================
            fw.write("  <div class='custom-tab-panel active' id='chartsPanel'>\n")
            fw.write("    <div class='card shadow-sm' style='border-radius: 12px; border:none;'>\n")
            fw.write("      <div class='card-body p-4'>\n")
            fw.write("        <h5 class='font-weight-bold text-dark mb-2' style='letter-spacing:-0.5px;'><i class='fa fa-project-diagram mr-2' style='color:#4f46e5;'></i>Interactive Motif Distribution Profile</h5>\n")
            fw.write("        <p class='text-muted small mb-4'>Each lane tracks an input molecule. The smooth heat-gradient highlights cluster hot-spots. <b>Lollipop heights represent the motif coverage value</b>. <span style='color:#4f46e5;'><i class='fa fa-hand-pointer mr-1'></i>Click a lollipop to jump to its binding site in the Sequences Match tab.</span></p>\n")
            num_rnas = len(seq_to_sign_motifs_dict)
            div_height = max(450, num_rnas * 65)
            fw.write(f"        <div id='plotlyLollipopChart' style='width:100%; min-height:{div_height}px;'></div>\n")
            fw.write("      </div>\n")
            fw.write("    </div>\n")
            fw.write("  </div>\n")

            fw.write("</div>\n")

            tab1.close()
            tab2.close()

            # STRUTTURAZIONE DATI PLOTLY (PYTHON)
            lollipop_data = []
            for single_input in seq_to_sign_motifs_dict:
                rna_length = len_dict.get(single_input, 100)
                bin_size = 15
                num_bins = max(1, int(rna_length / bin_size))
                
                motifs_list = []
                for m in seq_to_sign_motifs_dict[single_input]:
                    try:
                        start = int(total_file_dict[m][single_input][3])
                        end = int(total_file_dict[m][single_input][4])
                        center = (start + end) / 2
                        protein = m.split("_")[1]
                        
                        if m in motif_results_dict.get('nuc', {}):
                            str_or_nuc_key = 'nuc'
                            motif_type = "Sequence"
                        elif m in motif_results_dict.get('str', {}):
                            str_or_nuc_key = 'str'
                            motif_type = "Structure"
                        else:
                            str_or_nuc_key = 'str'
                            motif_type = "Structure"
                            for k in motif_results_dict.get('nuc', {}):
                                if k.split('.')[0] == m.split('.')[0]:
                                    str_or_nuc_key = 'nuc'
                                    motif_type = "Sequence"
                                    break
                        
                        target_dict = motif_results_dict.get(str_or_nuc_key, {})
                        motif_data = [0.6, 0, 0.03] 
                        
                        if m in target_dict: motif_data = target_dict[m]
                        else:
                            for k in target_dict:
                                if k in m or m in k or k.split('.')[0] == m.split('.')[0]:
                                    motif_data = target_dict[k]
                                    break
                        
                        p_val_real = float("%.2g" % motif_data[2])
                        cov_real = float("%.2g" % motif_data[0])
                        
                        motifs_list.append({
                            "start": start, "end": end, "center": center, "protein": protein,
                            "motif_id": m[:-4] if '.' in m else m, "motif_type": motif_type,
                            "pvalue": p_val_real, "coverage": cov_real
                        })
                    except Exception:
                        continue
                
                display_id = single_input.split(" ")[0]
                if len(display_id) > 40: display_id = display_id[:38] + "..."

                lollipop_data.append({
                    "rna_id": single_input, "display_id": display_id, "length": rna_length,
                    "bin_size": bin_size, "num_bins": num_bins, "motifs": motifs_list
                })

            json_lollipop_data = json.dumps(lollipop_data)
            json_child_tables = json.dumps(child_tables_dict)

            # INIEZIONE ASSETS ESTESI
            fw.write("\n\n")
            fw.write("<link rel='stylesheet' type='text/css' href='https://cdn.datatables.net/1.13.5/css/dataTables.bootstrap4.min.css'>\n")
            fw.write("<script src='https://cdn.plot.ly/plotly-2.24.1.min.js'></script>\n")
            fw.write("<script type='text/javascript' src='https://cdn.datatables.net/1.13.5/js/jquery.dataTables.min.js'></script>\n")
            fw.write("<script type='text/javascript' src='https://cdn.datatables.net/1.13.5/js/dataTables.bootstrap4.min.js'></script>\n")

            fw.write("<script>\n")
            fw.write(f"var rawChartData = {json_lollipop_data};\n")
            fw.write(f"var childTableHTML = {json_child_tables};\n")
            fw.write("var seqTable = null;\n")

            fw.write("function switchTab(panelId, btnId) {\n")
            fw.write("    $('.custom-tab-panel').removeClass('active');\n")
            fw.write("    $('#' + panelId).addClass('active');\n")
            fw.write("    $('#resultsTabs .btn-link').addClass('text-secondary').removeClass('active');\n")
            fw.write("    $('#' + btnId).addClass('active').removeClass('text-secondary');\n")
            fw.write("    if(panelId === 'chartsPanel') { Plotly.Plots.resize('plotlyLollipopChart'); }\n")
            fw.write("}\n")

            # --- NAVIGAZIONE DAL GRAFICO AL BINDING SITE IN SEQUENCES MATCH ---
            fw.write("function openSequenceForMotif(info) {\n")
            fw.write("    if(!info) return;\n")
            fw.write("    switchTab('sequencesPanel', 'btn-sequences');\n")
            fw.write("    if(!seqTable) return;\n")
            fw.write("    try { seqTable.columns.adjust(); } catch(e) {}\n")
            # trova la riga padre (la molecola RNA) qualunque sia la sua pagina
            fw.write("    var targetNode = null;\n")
            fw.write("    seqTable.rows().every(function() {\n")
            fw.write("        var node = this.node();\n")
            fw.write("        var ctrl = $(node).find('td.details-control');\n")
            fw.write("        if(ctrl.length && ctrl.attr('data-rna') === info.rna) { targetNode = node; }\n")
            fw.write("    });\n")
            fw.write("    if(!targetNode) return;\n")
            # porta la tabella sulla pagina che contiene quella riga
            fw.write("    var rowApi = seqTable.row(targetNode);\n")
            fw.write("    var pos = seqTable.rows({order: 'current'}).indexes().indexOf(rowApi.index());\n")
            fw.write("    if(pos >= 0) {\n")
            fw.write("        var page = Math.floor(pos / seqTable.page.len());\n")
            fw.write("        if(seqTable.page() !== page) { seqTable.page(page).draw(false); }\n")
            fw.write("    }\n")
            # espandi la riga figlia se non è già aperta
            fw.write("    var tr = $(targetNode);\n")
            fw.write("    if(!rowApi.child.isShown()) {\n")
            fw.write("        rowApi.child(childTableHTML[info.rna]).show();\n")
            fw.write("        tr.addClass('shown');\n")
            fw.write("        var pValCut = parseFloat($('#pvalueFilterSelect').val());\n")
            fw.write("        var covCut = parseFloat($('#coverageFilterSelect').val());\n")
            fw.write("        applyFiltersToChildTables(pValCut, covCut);\n")
            fw.write("    }\n")
            # scorri fino al binding site esatto ed evidenzialo
            fw.write("    setTimeout(function() {\n")
            fw.write("        var childRow = null;\n")
            fw.write("        tr.next('tr').find('tr.child-motif-row').each(function() {\n")
            fw.write("            if($(this).attr('data-start') === String(info.start) &&\n")
            fw.write("               $(this).attr('data-end') === String(info.end) &&\n")
            fw.write("               $(this).attr('data-protein') === String(info.protein) &&\n")
            fw.write("               (!info.type || $(this).attr('data-type') === String(info.type))) {\n")
            fw.write("                childRow = $(this); return false;\n")
            fw.write("            }\n")
            fw.write("        });\n")
            fw.write("        var scrollTarget = (childRow && childRow.length) ? childRow : tr;\n")
            fw.write("        if(scrollTarget && scrollTarget.length && scrollTarget[0].scrollIntoView) {\n")
            fw.write("            scrollTarget[0].scrollIntoView({behavior: 'smooth', block: 'center'});\n")
            fw.write("        }\n")
            fw.write("        if(childRow && childRow.length) {\n")
            fw.write("            childRow.css('transition', 'background-color 0.4s ease');\n")
            fw.write("            childRow.css('background-color', '#fde68a');\n")
            fw.write("            setTimeout(function() { childRow.css('background-color', ''); }, 2400);\n")
            fw.write("        }\n")
            fw.write("    }, 300);\n")
            fw.write("}\n")
            
            # --- AGGIORNAMENTO DEL TESTO DELLO SLIDER IN TEMPO REALE ---
            fw.write("function updateCoverageLabel(val) {\n")
            fw.write("    $('#covLabel').text('> ' + Math.round(val * 100) + '%');\n")
            fw.write("}\n")

            fw.write("function applyFiltersToChildTables(pValCut, covCut) {\n")
            fw.write("    $('#sequencesTable tbody tr.child-motif-row').each(function() {\n")
            fw.write("        var pVal = parseFloat($(this).attr('data-pvalue') || 1);\n")
            fw.write("        var cov = parseFloat($(this).attr('data-coverage') || 0);\n")
            fw.write("        if(pVal <= pValCut && cov >= covCut) { $(this).show(); } else { $(this).hide(); }\n")
            fw.write("    });\n")
            fw.write("}\n")

            fw.write("function applyFilters() {\n")
            fw.write("    var pValCut = parseFloat($('#pvalueFilterSelect').val());\n")
            fw.write("    var covCut = parseFloat($('#coverageFilterSelect').val());\n")
            
            fw.write("    $.fn.dataTable.ext.search.pop(); // Rimuove eventuali filtri precedenti\n")
            fw.write("    $.fn.dataTable.ext.search.push(function(settings, data, dataIndex, rowData, counter) {\n")
            fw.write("        if(settings.nTable.id !== 'enrichedTable') return true;\n")
            fw.write("        var row = settings.aoData[dataIndex].nTr;\n")
            fw.write("        var pVal = parseFloat($(row).attr('data-pvalue') || 1);\n")
            fw.write("        var cov = parseFloat($(row).attr('data-coverage') || 0);\n")
            fw.write("        return (pVal <= pValCut && cov >= covCut);\n")
            fw.write("    });\n")
            fw.write("    if($.fn.DataTable.isDataTable('#enrichedTable')) {\n")
            fw.write("        $('#enrichedTable').DataTable().draw();\n")
            fw.write("    }\n")
            
            fw.write("    applyFiltersToChildTables(pValCut, covCut);\n")
            fw.write("    buildPlotlyChart(pValCut, covCut);\n")
            fw.write("}\n")

            fw.write("function buildPlotlyChart(pvalueMax, coverageMin) {\n")
            fw.write("    var figData = [];\n")
            fw.write("    var layoutShapes = [];\n")
            fw.write("    var layoutAnnotations = [];\n")
            fw.write("    var numRnas = rawChartData.length;\n")
            
            fw.write("    var totalAvailableDomain = 1.0;\n")
            fw.write("    var gap = 0.04;\n")
            fw.write("    var trackHeight = (totalAvailableDomain - (gap * (numRnas - 1))) / numRnas;\n")
            
            fw.write("    rawChartData.forEach(function(track, idx) {\n")
            fw.write("        var yAxisNum = idx === 0 ? '' : (idx + 1);\n")
            fw.write("        var xAxisNum = idx === 0 ? '' : (idx + 1);\n")
            
            fw.write("        var filteredMotifs = track.motifs.filter(function(m) { return m.pvalue <= pvalueMax && m.coverage >= coverageMin; });\n")
            
            fw.write("        var dProfile = new Array(track.num_bins).fill(0);\n")
            fw.write("        filteredMotifs.forEach(function(m) {\n")
            fw.write("            var bIdx = Math.min(track.num_bins - 1, Math.floor(m.center / track.bin_size));\n")
            fw.write("            dProfile[bIdx] += 1;\n")
            fw.write("        });\n")
            
            fw.write("        var xMatrix = [];\n")
            fw.write("        for(var b=0; b<dProfile.length; b++) { xMatrix.push(b * track.bin_size + (track.bin_size/2)); }\n")
            fw.write("        figData.push({\n")
            fw.write("            x: xMatrix, y: [0], z: [dProfile], type: 'heatmap',\n")
            fw.write("            colorscale: [[0, '#f8fafc'], [0.1, '#f1f5f9'], [0.4, '#cbd5e1'], [0.8, '#94a3b8'], [1.0, '#64748b']],\n")
            fw.write("            showscale: idx === 0, zmin: 0, zmax: 4, zsmooth: 'best',\n")
            fw.write("            colorbar: idx === 0 ? { title: 'Local Density', thickness: 14, len: 0.5, y: 0.5, outlinecolor: 'transparent' } : undefined,\n")
            fw.write("            hoverinfo: 'skip', xaxis: 'x' + xAxisNum, yaxis: 'y' + yAxisNum\n")
            fw.write("        });\n")
            
            fw.write("        var seqX = [], seqY = [], seqText = [], seqCustom = [];\n")
            fw.write("        var strX = [], strY = [], strText = [], strCustom = [];\n")
            
            fw.write("        filteredMotifs.forEach(function(motif) {\n")
            fw.write("            var stemTop = 0.2 + (motif.coverage * 0.9);\n")
            fw.write("            var stemColor = motif.motif_type === 'Sequence' ? '#6ee7b7' : '#fca5a5';\n")
            fw.write("            layoutShapes.push({\n")
            fw.write("                type: 'line', xref: 'x' + xAxisNum, yref: 'y' + yAxisNum,\n")
            fw.write("                x0: motif.center, x1: motif.center, y0: 0.1, y1: stemTop,\n")
            fw.write("                line: { color: stemColor, width: 2.5 }\n")
            fw.write("            });\n")
            
            fw.write("            var hText = '<b>Motif:</b> ' + motif.motif_id + '<br>' +\n")
            fw.write("                        '<b>Protein:</b> ' + motif.protein + '<br>' +\n")
            fw.write("                        '<b>Coverage:</b> ' + (motif.coverage * 100).toFixed(0) + '%<br>' +\n")
            fw.write("                        '<b>p-value:</b> ' + motif.pvalue + '<br>' +\n")
            fw.write("                        '<b>Coordinates:</b> ' + motif.start + '-' + motif.end + ' nt';\n")
            
            fw.write("            var cData = { rna: track.rna_id, protein: motif.protein, start: motif.start, end: motif.end, type: motif.motif_type };\n")
            fw.write("            if(motif.motif_type === 'Sequence') {\n")
            fw.write("                seqX.push(motif.center); seqY.push(stemTop); seqText.push(hText); seqCustom.push(cData);\n")
            fw.write("            } else {\n")
            fw.write("                strX.push(motif.center); strY.push(stemTop); strText.push(hText); strCustom.push(cData);\n")
            fw.write("            }\n")
            fw.write("        });\n")
            
            fw.write("        if(seqX.length > 0) {\n")
            fw.write("            figData.push({ x: seqX, y: seqY, text: seqText, customdata: seqCustom, hoverinfo: 'text', mode: 'markers', name: 'Sequence Motif', showlegend: idx === 0, marker: { color: '#10b981', size: 11, symbol: 'circle', line: {color: '#ffffff', width: 1.5} }, xaxis: 'x' + xAxisNum, yaxis: 'y' + yAxisNum });\n")
            fw.write("        }\n")
            fw.write("        if(strX.length > 0) {\n")
            fw.write("            figData.push({ x: strX, y: strY, text: strText, customdata: strCustom, hoverinfo: 'text', mode: 'markers', name: 'Structure Motif', showlegend: idx === 0, marker: { color: '#f43f5e', size: 11, symbol: 'circle', line: {color: '#ffffff', width: 1.5} }, xaxis: 'x' + xAxisNum, yaxis: 'y' + yAxisNum });\n")
            fw.write("        }\n")
            
            fw.write("        layoutAnnotations.push({\n")
            fw.write("            text: '<b>' + track.display_id + '</b>', showarrow: false,\n")
            fw.write("            xref: 'paper', yref: 'y' + yAxisNum, x: -0.01, y: 0.15, xanchor: 'right', font: { size: 11, color: '#334155' }\n")
            fw.write("        });\n")
            fw.write("    });\n")

            fw.write("    var maxLabelLen = 0;\n")
            fw.write("    rawChartData.forEach(function(t) { if(t.display_id && t.display_id.length > maxLabelLen) maxLabelLen = t.display_id.length; });\n")
            fw.write("    var leftMargin = Math.min(340, Math.max(160, Math.round(maxLabelLen * 7.5) + 30));\n")
            fw.write("    var layout = {\n")
            fw.write("        hovermode: 'closest', grid: { rows: numRnas, columns: 1, pattern: 'independent' },\n")
            fw.write("        shapes: layoutShapes, annotations: layoutAnnotations,\n")
            fw.write("        legend: { orientation: 'h', x: 0.5, xanchor: 'center', y: -0.15, font: {size:12} },\n")
            fw.write("        margin: { l: leftMargin, r: 40, t: 30, b: 80 }, plot_bgcolor: '#ffffff', paper_bgcolor: '#ffffff'\n")
            fw.write("    };\n")
            
            fw.write("    rawChartData.forEach(function(track, idx) {\n")
            fw.write("        var yAxisNum = idx === 0 ? '' : (idx + 1);\n")
            fw.write("        var xAxisNum = idx === 0 ? '' : (idx + 1);\n")
            
            fw.write("        var dStart = idx * (trackHeight + gap);\n")
            fw.write("        var dEnd = dStart + trackHeight;\n")
            
            fw.write("        layout['yaxis' + yAxisNum] = { domain: [dStart, dEnd], showgrid: false, zeroline: false, showticklabels: false, range: [-0.3, 1.3] };\n")
            fw.write("        layout['xaxis' + xAxisNum] = { showgrid: true, gridcolor: '#f1f5f9', linecolor: '#e2e8f0', range: [0, track.length], title: idx === 0 ? { text: 'RNA Sequence Position (nucleotides)', standoff: 12 } : '' };\n")
            fw.write("    });\n")

            fw.write("    var config = { responsive: true, displaylogo: false, modeBarButtonsToRemove: ['select2d', 'lasso2d', 'autoScale2d', 'toggleSpikelines', 'hoverCompareCartesian'] };\n")
            fw.write("    Plotly.newPlot('plotlyLollipopChart', figData, layout, config);\n")
            fw.write("    var plotDiv = document.getElementById('plotlyLollipopChart');\n")
            fw.write("    if(plotDiv) {\n")
            fw.write("        if(plotDiv.removeAllListeners) { plotDiv.removeAllListeners('plotly_click'); }\n")
            fw.write("        plotDiv.on('plotly_click', function(evt) {\n")
            fw.write("            if(!evt || !evt.points || !evt.points.length) return;\n")
            fw.write("            var cd = evt.points[0].customdata;\n")
            fw.write("            if(cd) { openSequenceForMotif(cd); }\n")
            fw.write("        });\n")
            fw.write("    }\n")
            fw.write("}\n")

            fw.write("$(document).ready(function() {\n")
            fw.write("    $('#enrichedTable').DataTable({ 'pageLength': 10, 'order': [[4, 'asc']] });\n")

            # --- LIGHTBOX PER I LOGO DELLA COLONNA LOGO (ENRICHED MOTIFS) ---
            fw.write("    $('#enrichedTable').on('click', 'img.logo-zoomable', function() {\n")
            fw.write("        $('#logoLightboxImg').attr('src', $(this).attr('src'));\n")
            fw.write("        $('#logoLightboxCaption').text($(this).attr('data-caption') || '');\n")
            fw.write("        $('#logoLightbox').addClass('open');\n")
            fw.write("    });\n")
            fw.write("    $('#logoLightbox').on('click', function(e) {\n")
            fw.write("        if(e.target.id !== 'logoLightboxImg') { $(this).removeClass('open'); }\n")
            fw.write("    });\n")
            fw.write("    $(document).on('keydown', function(e) {\n")
            fw.write("        if(e.key === 'Escape') { $('#logoLightbox').removeClass('open'); }\n")
            fw.write("    });\n")
            
            fw.write("    seqTable = $('#sequencesTable').DataTable({\n")
            fw.write("        'pageLength': 25,\n") 
            fw.write("        'order': [[1, 'asc']],\n")
            fw.write("        'columnDefs': [{ 'targets': 0, 'orderable': false }]\n")
            fw.write("    });\n")

            fw.write("    $('#sequencesTable tbody').on('click', 'td.details-control', function () {\n")
            fw.write("        var tr = $(this).closest('tr');\n")
            fw.write("        var row = seqTable.row(tr);\n")
            fw.write("        var rnaId = $(this).attr('data-rna');\n")
            fw.write("        if (row.child.isShown()) {\n")
            fw.write("            row.child.hide();\n")
            fw.write("            tr.removeClass('shown');\n")
            fw.write("        } else {\n")
            fw.write("            row.child(childTableHTML[rnaId]).show();\n")
            fw.write("            tr.addClass('shown');\n")
            fw.write("            var pValCut = parseFloat($('#pvalueFilterSelect').val());\n")
            fw.write("            var covCut = parseFloat($('#coverageFilterSelect').val());\n")
            fw.write("            applyFiltersToChildTables(pValCut, covCut);\n")
            fw.write("        }\n")
            fw.write("    });\n")

            fw.write("    applyFilters();\n")
            fw.write("});\n")
            fw.write("</script>\n")

            fw.write("</div>\n")

            try:
                shutil.make_archive(os.path.join(os.path.dirname(dir_user_download), "download"), 'zip', dir_user_download)
            except Exception:
                pass
        else:
            fw.write("<div class='container my-5 text-center'><div class='alert alert-light border py-5 shadow-sm'><h2 class='text-muted'><i class='fa fa-folder-open mb-3 d-block text-secondary' style='font-size:3rem;'></i>Sorry, no significant results found.</h2><p class='text-secondary mb-0'>Try lowering your input filtering or check candidate sequence formats.</p></div></div>")
            fw.write("</div>\n")

    if user_email != '':
        try:
            my_email.send_email_with_code(code=user, user_email=user_email)
        except Exception:
            pass
