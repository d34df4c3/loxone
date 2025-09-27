// create function to check if the document has been saved
function isNewDocument(frm)
{
    return frm.doc.creation == undefined
}

function addButton_ChangeKeycode(frm)
{
    if (isNewDocument(frm))
        return;

    function call_save_user_keycode(keycode) {
        frappe.call('loxone.save_user_keycode', {
            ms_name: frm.doc.lx_miniserver,
            user_name: frm.doc.name,
            keycode: keycode
        }).then(r => {
                frappe.msgprint({
                    indicator: 'green',
                    message: 'Keycode changed successfully.'
                });
                frm.reload_doc();
            })
    }

    frm.add_custom_button('Change Keycode', function()
    {
        frappe.prompt('Enter new keycode', ({ value }) => {
            // Validate new_keycode: must be string of digits, length 2-8
            if (/^\d{2,8}$/.test(value)) {
                call_save_user_keycode(value);
            } else {
                frappe.msgprint({
                    indicator: 'red',
                    message: 'Keycode must be 2 to 8 digits.'
                });
            }
        });
        return;
        
    });
}

frappe.ui.form.on('Loxone User', {
    refresh: function(frm) {

        addButton_ChangeKeycode(frm);

        frm.add_custom_button('Debug', function() {
            console.log(frm)
        });
    }
});
