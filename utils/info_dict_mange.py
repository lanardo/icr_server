from utils.binary_object import img2binary, pdf2binary

EMP = ""
MANDATORY = "MAN"


class InfoDictManage:

    def __init__(self):
        pass

    def append(self, parent, key, value=EMP, mandatory=False):
        if mandatory:
            parent[key] = value
        if mandatory is False:
            if value == EMP:
                pass
            else:
                if type(value) == dict:
                    is_empty_dict = True
                    for sub_val in value.values():
                        if sub_val != EMP:
                            is_empty_dict = False
                            break
                    if is_empty_dict:
                        pass
                    else:
                        parent[key] = value
                else:
                    parent[key] = value

    def reformat_info_dict(self, validated_info, template, binary=EMP):
        company = validated_info['company']
        invoice_details = validated_info['invoice_details']
        invoice_lines = validated_info['invoice_lines']
        invoice_tax = validated_info['invoice_tax']
        invoice_total = validated_info['invoice_total']
        validated = validated_info['validated']

        # ====================================================================================================
        payment_details = {}
        self.append(parent=payment_details, key="Invoice nr", value=invoice_details["InvoiceNumber"], mandatory=True)
        self.append(parent=payment_details, key="Invoice nr", value=invoice_details["InvoiceNumber"], mandatory=True)  # MANDATORY
        self.append(parent=payment_details, key="Issue date", value=invoice_details["InvoiceIssueDate"], mandatory=True)  # MANDATORY
        self.append(parent=payment_details, key="Free text", value=invoice_details["FreeText"])
        self.append(parent=payment_details, key="Tax currency")
        _invoice_period = {}
        self.append(_invoice_period, "Start data")
        self.append(_invoice_period, "End date")
        self.append(parent=payment_details, key="Invoice Period", value=_invoice_period)
        self.append(parent=payment_details, key="Order reference", value=invoice_details["OrderReference"])
        _doc_reference = {}
        self.append(_doc_reference, "ID")
        self.append(_doc_reference, "Document type")
        self.append(parent=payment_details, key="Contract document reference", value=_doc_reference)
        _delivery = {}
        self.append(_delivery, "Street")
        self.append(_delivery, "Additional street")
        self.append(_delivery, "City")
        self.append(_delivery, "Postal zone")
        self.append(parent=payment_details, key="Delivery details", value=_delivery)
        self.append(parent=payment_details, key="Due date", value= invoice_details["InvoiceDueDate"], mandatory=True)
        self.append(parent=payment_details, key="ID", value=invoice_details["TransactionID"], mandatory=True)
        self.append(parent=payment_details, key="Tax currency")
        self.append(parent=payment_details, key="Discount")
        self.append(parent=payment_details, key="Fees")

        # ====================================================================================================
        _tax_totals = {}
        self.append(_tax_totals, "Total VAT amount", invoice_tax["TaxValue"], True)
        self.append(parent=payment_details, key="Tax totals", value=_tax_totals)
        _tax_sub_totals = {}
        self.append(_tax_sub_totals, "Taxable amount")
        self.append(_tax_sub_totals, "Tax amount", invoice_tax["TaxValue"], True)
        self.append(_tax_sub_totals, "TAX percentage", invoice_tax["TaxType"], True)
        self.append(parent=payment_details, key="Tax sub-totals", value=_tax_sub_totals)

        # ====================================================================================================
        totals = {}
        self.append(parent=totals, key="Line extension amount", value=invoice_total["LineExtensionAmount"], mandatory=True)  # MANDATORY
        self.append(parent=totals, key="Tax exclusive amount", value=invoice_total["TotalExclusiveTAX"], mandatory=True)  # MANDATORY
        self.append(parent=totals, key="Allowances amount", value=invoice_total["SumOfDiscount"], mandatory=True)  # MANDATORY
        self.append(parent=totals, key="Prepaid amount", value=invoice_total["SumOfFees"], mandatory=True)  # MANDATORY
        self.append(parent=totals, key="Rounding", value=invoice_total["Rounding"], mandatory=True)  # MANDATORY
        self.append(parent=totals, key="Amount for payment", value=invoice_total["TotalInclusiveTAX"], mandatory=True)  # MANDATORY

        # ====================================================================================================
        lines = []
        components = template['info']['InvoiceLines']['components']
        meanings = [component['meaning'] for component in components]
        for invoice_line in invoice_lines:
            _line_idx = str(invoice_lines.index(invoice_line))
            _line = {}
            self.append(_line, "Note"),
            self.append(_line, "Quantity", invoice_line[meanings.index("Quantity")], True),
            self.append(_line, "Line total", invoice_line[meanings.index("TotalLineAmount")], True),
            self.append(_line, "Delivery date"),
            self.append(_line, "Delivery address"),
            self.append(_line, "Delivery additional address"),
            self.append(_line, "Delivery city"),
            self.append(_line, "Delivery postal zone"),
            self.append(_line, "Allowance/fee reason"),
            self.append(_line, "Allowance/fee amount"),
            self.append(_line, "Item name"),
            self.append(_line, "Item descrption", invoice_line[meanings.index("Description")]),
            self.append(_line, "Seller item ID", invoice_line[meanings.index("LineItemID")]),
            self.append(_line, "Tax percent", invoice_line[meanings.index("Discount")], True),
            self.append(_line, "Item price", invoice_line[meanings.index("Price")], True)

            lines.append({_line_idx: _line})

        # ==========================================================================================================
        attachments = {}
        if binary is not None:
            self.append(attachments, "Binary code", binary, mandatory=True)

        # ==========================================================================================================
        # ==========================================================================================================
        info_dict = {}
        self.append(parent=info_dict, key="Validator", value="No Errors" * validated_info['validated'], mandatory=True)
        self.append(parent=info_dict, key="Invoice rows", value=len(invoice_lines))
        self.append(parent=info_dict, key="Payment details", value=payment_details)
        self.append(parent=info_dict, key="Invoice totals", value=totals)
        self.append(parent=info_dict, key="Invoice line", value=lines)
        self.append(parent=info_dict, key="Attachments", value=attachments)

        return info_dict


if __name__ == '__main__':
    pass
