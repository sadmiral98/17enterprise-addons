/** @odoo-module */

import { Order } from "@point_of_sale/app/store/models";
import { patch } from "@web/core/utils/patch";

patch(Order.prototype, {
    setup() {
        super.setup(...arguments)
        this.card_no = null
    },
    update_card_no(card_no){
        this.card_no = card_no
    },
    //@override
    export_as_JSON() {
        let json = super.export_as_JSON(...arguments)
        json.statement_ids.forEach((item) => {
            item[2].card_no = this.card_no
            console.log(item)
        })
        return json
    }
});
