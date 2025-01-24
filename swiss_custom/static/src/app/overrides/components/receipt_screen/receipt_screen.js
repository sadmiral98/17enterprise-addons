/** @odoo-module **/

import { ReceiptScreen } from "@point_of_sale/app/screens/receipt_screen/receipt_screen";
import { patch } from "@web/core/utils/patch";
import { OrderReceipt } from "@point_of_sale/app/screens/receipt_screen/receipt/order_receipt";

patch(ReceiptScreen.prototype, {
    setup() {
        super.setup(...arguments)
    },
    async printReceipt() {
        super.printReceipt(...arguments)
        console.log("hello world")
        // Write print code here
    }
});