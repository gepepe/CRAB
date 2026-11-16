$(function () {

    //format popovers
    //$('[data-toggle="popover"]').popover();

    $('#format_pop_1').popover({
        html: true,
        content: 'input sequences are accepted in multiFASTA format\
        and are parsed as blocks. For each sequence:\
  			<ul><li>The line containing the name and/or the description of the \
  			sequence starts with a ">";</li><li> \
			The words following the ">" are interpreted as the RNA id;</li><li>\
			The subsequent line(s) should be the RNA nucleotide sequence. \
      Multiline FASTA are accepted;</li><li>\
			The subsequent block can contain secondary structure information (Optional\
			in dot-bracket);</li></ul>\
			<em>(click again to dismiss)</em>',
        placement: 'right'
    });

    $(".chosen-select").chosen({
        no_results_text: "Oops, nothing found!"
    });

    //populate text area with examples
    $("#ex_w_str").click(function () {
        $("#inputRNA").val(
        );
        /*$.ajax({
            url: "examples/example_w_struct.txt",
            dataType: "text",
            success: function (data) {
                $("#inputRNA").val(data);
            }
        });*/
    });
    $("#ex_wo_str").click(function () {
        $("#inputRNA").val(
">hsa-let-7a-1_pre-miRNA\n" +
"UGGGAUGAGGUAGUAGGUUGUAUAGUUUUAGGGUCACACCCACCACUGGGAGAUAACUAUACAAUCUACUGUCUUUCCUA\n" +
">hsa-let-7a-2_pre-miRNA\n" +
"AGGUUGAGGUAGUAGGUUGUAUAGUUUAGAAUUACAUCAAGGGAGAUAACUGUACAGCCUCCUAGCUUUCCU\n" +
">hsa-let-7a-3_pre-miRNA\n" +
"GGGUGAGGUAGUAGGUUGUAUAGUUUGGGGCUCUGCCCUGCUAUGGGAUAACUAUACAAUCUACUGUCUUUCCU\n" +
">hsa-let-7b_pre-miRNA\n" +
"CGGGGUGAGGUAGUAGGUUGUGUGGUUUCAGGGCAGUGAUGUUGCCCCUCGGAAGAUAACUAUACAACCUACUGCCUUCCCUG\n" +
">hsa-let-7c_pre-miRNA\n" +
"GCAUCCGGGUUGAGGUAGUAGGUUGUAUGGUUUAGAGUUACACCCUGGGAGUUAACUGUACAACCUUCUAGCUUUCCUUGGAGC\n" +
">hsa-let-7d_pre-miRNA\n" +
"CCUAGGAAGAGGUAGUAGGUUGCAUAGUUUUAGGGCAGGGAUUUUGCCCACAAGGAGGUAACUAUACGACCUGCUGCCUUUCUUAGG\n" +
">hsa-let-7e_pre-miRNA\n" +
"CCCGGGCUGAGGUAGGAGGUUGUAUAGUUGAGGAGGACACCCAAGGAGAUCACUAUACGGCCUCCUAGCUUUCCCCAGG\n" +
">hsa-let-7f-1_pre-miRNA\n" +
"UCAGAGUGAGGUAGUAGAUUGUAUAGUUGUGGGGUAGUGAUUUUACCCUGUUCAGGAGAUAACUAUACAAUCUAUUGCCUUCCCUGA\n" +
">hsa-let-7f-2_pre-miRNA\n" +
"UGUGGGAUGAGGUAGUAGAUUGUAUAGUUUUAGGGUCAUACCCCAUCUUGGAGAUAACUAUACAGUCUACUGUCUUUCCCAC\n" +
">hsa-let-7g_pre-miRNA\n" +
"CAAUCUGAGGUAGUAGUUUGUACAGUUUGAGGGUCUAUGAUACCACCCGGUACAGGAGAUAACUGUACAGCCUCCUAGCUUUCCU"        );
        /*$.ajax({
            $("#inputRNA").val("A");
            url: "examples/example_wo_struct.txt",
            dataType: "text",
            success: function (data) {
                $("#inputRNA").val(data);
            }
        });*/
    });

});

$(function () {
  const $sel = $('#options_experiments');

  $sel.on('change', function () {
    let vals = $sel.val() || [];

    // Se clicco "Select all": seleziona tutto tranne global e __all__
    if (vals.includes('__all__')) {
      const allExceptGlobal = $sel.find('option').map(function () {
        return this.value;
      }).get().filter(v => v !== '__all__' && v !== 'global');

      $sel.val(allExceptGlobal);
      $sel.trigger('chosen:updated');
      return;
    }

    // (Optional ma consigliato) global esclusivo:
    // se scelgo global insieme ad altri -> tengo solo global
    if (vals.includes('global') && vals.length > 1) {
      $sel.val(['global']);
      $sel.trigger('chosen:updated');
      return;
    }

    // se scelgo altri mentre global è selezionato -> tolgo global
    if (!vals.includes('global')) {
      // ok, nulla
    }
  });
});
