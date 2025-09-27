// create function to check if the document has been saved
function isNewDocument(frm)
{
    return frm.doc.creation == undefined
}

function addButton_LoadUserGroups(frm)
{
    if (isNewDocument(frm))
        return;

    frm.add_custom_button('Load User Groups', function()
    {
        frappe.call('loxone.load_user_groups', {ms_name: frm.doc.name})
            .then(r => {
                frappe.msgprint({
                    indicator: 'green',
                    title: 'User Groups loaded successfully.',
                    message: 'Check the <a href="/app/loxone-user-group?lx_miniserver=' + frm.doc.name + '">Loxone User Group (' + frm.doc.name + ')</a>'
                });
            })
    }, 'Loxone Actions');
}

function addButton_LoadUsers(frm)
{
    if (isNewDocument(frm))
        return;

    frm.add_custom_button('Load Users', function()
    {
        frappe.call('loxone.load_users', {ms_name: frm.doc.name})
            .then(r => {
                frappe.msgprint({
                    indicator: 'green',
                    title: 'Users loaded successfully.',
                    message: 'Check the <a href="/app/loxone-user?lx_miniserver=' + frm.doc.name + '">Loxone User (' + frm.doc.name + ')</a>'
                });
            })
    }, 'Loxone Actions');
}

addButton_CheckConnection = function(frm) {
    frm.add_custom_button('Check Connection', function()
    {
        frappe.call('loxone.check_connection', {
            url: frm.doc.lx_conn_url,
            user: frm.doc.lx_conn_user,
            password: frm.doc.lx_conn_password
        }).then(r => {
                    frappe.msgprint({
                        indicator: 'green',
                        message: 'Connection to Miniserver is OK. ('+ r.message +')'
                    });
                }
        )
    });
}

frappe.ui.form.on('Miniserver', {
    refresh: function(frm) {

        addButton_CheckConnection(frm);
        
        addButton_LoadUserGroups(frm);
        addButton_LoadUsers(frm);

        frm.add_custom_button('Debug', function() {
            console.log(frm)
        });
    }
});
