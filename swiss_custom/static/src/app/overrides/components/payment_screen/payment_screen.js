/** @odoo-module */

import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { useRef } from "@odoo/owl";
import { patch } from "@web/core/utils/patch";
import { usePos } from "@point_of_sale/app/store/pos_hook";

patch(PaymentScreen.prototype, {
    setup() {
        super.setup(...arguments)
        this.card_no_text = useRef("card_no_input")
        this.pos = usePos()
    },
    async _updateCardNo(event){
        // console.log('hello world')
        this.pos.update_card_no(this.card_no_text.el.value)
    },
    toggleIsToInvoice() {
        super.toggleIsToInvoice(...arguments)
        console.log('hello world')
    }
});
