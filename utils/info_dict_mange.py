from utils.binary_object import img2binary, pdf2binary

EMP = ""
MANDATORY = "MAN"


class InfoDictManage:

    def __init__(self):
        self.info_dict = {}

    def reformat_info_dict(self, validated_info, template, binary=None):
        company = validated_info['company']
        invoice_details = validated_info['invoice_details']
        invoice_lines = validated_info['invoice_lines']
        invoice_tax = validated_info['invoice_tax']
        invoice_total = validated_info['invoice_total']
        validated = validated_info['validated']

        self.__parent(key="Invoice nr", val=invoice_details["InvoiceNumber"], mandatory=True)  # MANDATORY
        self.__parent(key="Issue date", val=invoice_details["InvoiceIssueDate"], mandatory=True)  # MANDATORY
        self.__parent(key="Free text", val=invoice_details["FreeText"])
        self.__parent("Tax currency")
        self.__parent("Invoice Period", [("Start data", EMP, False),
                                         ("End date", EMP, False)])
        self.__parent(key="Order reference", val=invoice_details["OrderReference"])
        self.__parent("Contract document reference", [("ID", EMP, False),
                                                      ("Document type", EMP, False)])

        if binary is not None:
            binary_objs = binary
        else:
            binary_objs = EMP

        self.__parent(key="Attachments", val=[("Binary object", binary_objs, False)])  # MANDATORY

        self.__parent("Delivery details", [("Date", EMP, False),
                                           ("Street", EMP, False),
                                           ("Additional street", EMP, False),
                                           ("City", EMP, False),
                                           ("Postal zone", EMP, False)])

        self.__parent(key="Payment details", val=[("Due date", invoice_details["InvoiceDueDate"], True),  # MANDATORY
                                                  ("ID", invoice_details["TransactionID"], True)])        # MANDATORY

        self.__parent("Payment terms")
        self.__parent("Discount")
        self.__parent("Fees")
        self.__parent("Tax totals", [("Total VAT amount", invoice_tax["TaxValue"], True)])
        self.__parent(key="Tax sub-totals", val=[("Taxable amount", MANDATORY, False),
                                                 ("Tax amount", invoice_tax["TaxValue"], True),
                                                 ("TAX percentage", invoice_tax["TaxType"], True)])

        self.__parent(key="Line extension amount", val=invoice_total["LineExtensionAmount"], mandatory=True)  # MANDATORY
        self.__parent(key="Tax exclusive amount", val=invoice_total["TotalExclusiveTAX"], mandatory=True)  # MANDATORY
        self.__parent(key="Allowances amount", val=invoice_total["SumOfDiscount"], mandatory=True)  # MANDATORY
        self.__parent(key="Prepaid amount", val=invoice_total["SumOfFees"], mandatory=True)  # MANDATORY
        self.__parent(key="Rounding", val=invoice_total["Rounding"], mandatory=True)  # MANDATORY
        self.__parent(key="Amount for payment", val=invoice_total["TotalInclusiveTAX"], mandatory=True)  # MANDATORY

        components = template['info']['InvoiceLines']['components']
        meanings = [component['meaning'] for component in components]
        lines = []
        for invoice_line in invoice_lines:
            line_key = str(invoice_lines.index(invoice_line))
            line_val = (
                self.__child(
                    [("Note", EMP, False),
                     ("Quantity", invoice_line[meanings.index("Quantity")], True),
                     ("Line total", invoice_line[meanings.index("TotalLineAmount")], True),
                     ("Delivery date", EMP, False),
                     ("Delivery address", EMP, False),
                     ("Delivery additional address", EMP, False),
                     ("Delivery city", EMP, False),
                     ("Delivery postal zone", EMP, False),
                     ("Allowance/fee reason", EMP, False),
                     ("Allowance/fee amount", EMP, False),
                     ("Item name", EMP, False),
                     ("Item descrption", invoice_line[meanings.index("Description")], False),
                     ("Seller item ID", invoice_line[meanings.index("LineItemID")], False),
                     ("Tax percent", invoice_line[meanings.index("Discount")], True),
                     ("Item price", invoice_line[meanings.index("Price")], True)]
                )
            )
            lines.append((line_key, line_val, False))
        self.__parent(key="Invoice line", val=lines)

        return self.info_dict

    def __parent(self, key, val=EMP, mandatory=False):
        if type(val) == list:
            val = self.__child(key_vals=val)

        if val != EMP:
            self.info_dict[key] = val
        elif mandatory:
            self.info_dict[key] = " "  # MANDATORY
        else:
            pass

    def __child(self, key_vals=None):
        parent_val = {}
        for i in range(len(key_vals)):
            key, val, mandatory = key_vals[i]
            if val != EMP:
                parent_val[key] = val
            elif mandatory:
                parent_val[key] = " "  # MANDATORY
            else:
                pass

        for key, value in parent_val.items():
            if parent_val[key] not in [EMP, MANDATORY]:
                return parent_val
        return EMP


if __name__ == '__main__':
    pass
