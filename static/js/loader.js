function preventSubmit(e){
    /* Prevent submit */
    e.preventDefault();
    return false;
}

/*Check if organization and network are selected. If not, prevent submit - If yes, show loading indicator*/
function submitDeleteForm(e){
    /* Check if organization and network are selected. If not, prevent submit*/
    var selected_organization = document.getElementById("organizations_select").value;

    if(selected_organization == "0"){
        return preventSubmit(e);
 
    }else{
        var selected_network = document.getElementById(selected_organization).getElementsByClassName("networks")[0].value;

        if(selected_network == "0" ){
            return preventSubmit(e);
            
        }else{
            /* Change submit button text */
            document.getElementById('submit_button').value = 'Processing the request ...'; 
            document.getElementById('delete_form').submit();        
        }  
    }
    
}

/*Check if organization and network are selected. If not, prevent submit - If yes, show loading indicator*/
function submitMigrationForm(e) {

    var selected_organization = document.getElementById("organizations_select").value;

    if(selected_organization == "0"){
        return preventSubmit(e);
 
    }else{
        var selected_network = document.getElementById(selected_organization).getElementsByClassName("networks")[0].value;

        if(selected_network == "0" ){
            return preventSubmit(e);
            
        }else{
            /* Change submit button text */
            document.getElementById("submit_button").value = "Processing the request ..."; 
        }  
    }
}

/* Show original text on page load - not processing the request */
function showOriginalText(originalButtonText){
    document.getElementById("submit_button").value = originalButtonText;
}



                          
  