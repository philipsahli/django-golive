$ ->
    $('button#submit').click =>
        val1 = $('input#val1').val()
        val2 = $('input#val2').val()
        console.log "send task"
        data = [val1, val2]
        console.log data
        $.ajax
            url: "/celerydemo/start/celerydemo.tasks.add/"
            data: {val1, val2}
            type: "POST"
            success: (data, textStatus, jqXHR) =>
                responseDate = jqXHR.getResponseHeader('Date')
                # error
                if data.error
                    $('#output').append "<div style='margin-bottom: 20px'><p style='color: red'><small>"+responseDate+" ERROR "+data.error+"</small></p></div>"
                # success
                else
                    $('#output').append "<div style='margin-bottom: 20px'><p style='color: green'><small>"+responseDate+" INFO Task started ("+data.id+")</small></p></div>"
                    check(data.id)

    # check task status periodically
    check = (id) ->
        state=false
        do check_state = () =>
            if state==false
                $.ajax
                    url: "/celerydemo/status/"+id+"/"
                    type: "GET"
                    success: (data, textStatus, jqXHR) ->
                        responseDate = jqXHR.getResponseHeader('Date')
                        console.log id
                        console.log data
                        $('#output').append "<div style='margin-bottom: 20px'><p style='color: green'><small>"+responseDate+" INFO Task done("+data.state+")</small></p></div>"
                        if (data.state=="SUCCESS")
                            state=true
            setTimeout check_state, 4000 unless state==true
