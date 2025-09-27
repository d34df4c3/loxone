// Check if the document has been saved
function isNewDocument(frm)
{
    return frm.doc.creation == undefined
}

function addButton_LoadUserGroups(frm)
{
    if (isNewDocument(frm))
        return;

    frm.add_custom_button('Load User Groups', () => {
        frappe.confirm(
            `Load user groups from Loxone for Miniserver: ${frm.doc.name}?
            <ul>
               <li>User groups that do not exist in Dokos will be created.</li>
               <li>Existing user groups in Dokos will be updated.</li>
               <li>If a user group has been deleted in Loxone, the deletion will NOT be applied in Dokos.</li>
            </ul>`,
            // On confirm
            () => {
                frappe.call({
                    method: 'loxone.load_user_groups',
                    args: { ms_name: frm.doc.name },
                    freeze: true,
                    freeze_message: 'Loading user groups…'
                })
                .then(() => {
                    frappe.msgprint({
                        indicator: 'green',
                        title: 'User Groups loaded successfully.',
                        message:
                            'Check the ' +
                            `<a href="/app/loxone-user-group?lx_miniserver=${encodeURIComponent(frm.doc.name)}">` +
                            `Loxone User Group (${frappe.utils.escape_html(frm.doc.name)})</a>`
                    });
                })
                .catch((err) => {
                    frappe.msgprint({
                        indicator: 'red',
                        title: 'Error',
                        message: `Failed to load user groups.${err && err.message ? ' ' + err.message : ''}`
                    });
                });
            },
            // On cancel: do nothing (dialog closes automatically)
            () => {}
        );
    }, 'Loxone Actions');

}

function addButton_LoadUsers(frm)
{
    if (isNewDocument(frm))
        return;

    frm.add_custom_button('Load Users', () => {
        frappe.confirm(
            `Load users from Loxone for Miniserver: ${frappe.utils.escape_html(frm.doc.name)}?
            <ul>
                <li>Users that do not exist in Dokos will be created.</li>
                <li>Existing users in Dokos will be updated.</li>
                <li>If a user has been deleted in Loxone, the user WILL be deleted in Dokos.</li>
                <li>Note this synchronization only impacts LoxoneUser Doctype, not ERPNext users.</li>
            </ul>`,
            // On confirm
            () => {
                frappe.call({
                    method: 'loxone.load_users',
                    args: { ms_name: frm.doc.name },
                    freeze: true,
                    freeze_message: 'Loading users…'
                })
                .then(() => {
                    const ms = frm.doc.name || '';
                    frappe.msgprint({
                        indicator: 'green',
                        title: 'Users loaded successfully.',
                        message:
                            'Check the ' +
                            `<a href="/app/loxone-user?lx_miniserver=${encodeURIComponent(ms)}">` +
                            `Loxone User (${frappe.utils.escape_html(ms)})</a>`
                    });
                })
                .catch((err) => {
                    frappe.msgprint({
                        indicator: 'red',
                        title: 'Error',
                        message: `Failed to load users.${err && err.message ? ' ' + err.message : ''}`
                    });
                });
            },
            // On cancel: do nothing (dialog closes automatically)
            () => {}
        );
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

frappe.ui.form.on('Loxone Miniserver', {
    refresh: function(frm) {

        addButton_CheckConnection(frm);
        
        addButton_LoadUserGroups(frm);
        addButton_LoadUsers(frm);

        frm.add_custom_button('Debug', function() {
            console.log(frm);
            frappe.show_alert({
                message: `A dump of the Frappe Form has been printed to the browser console.
                <br>Press F12 or Ctrl+Shift+I to open the console.`,
                indicator: 'blue'
            }, 8);
        });
    }
});
