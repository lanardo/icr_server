import json
import cv2
import base64


EMP = ""
MANDATORY = "MAN"


class InfoDictManage:

    def __init__(self):
        self.info_dict = {}

    def reformat_info_dict(self, validated_info, contents, template):
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

        binary_objs = []
        for content in contents:
            image = content['image']
            retval, buffer = cv2.imencode('.jpg', image)
            jpg_as_text = base64.b64encode(buffer)
            base_string = jpg_as_text.decode('utf-8')
            binary_objs.append(base_string)
        self.__parent(key="Attachments", val=[("Binary object", binary_objs, True)])  # MANDATORY

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
        self.__parent("Tax totals", [("Total VAT amount", MANDATORY, True)])
        self.__parent(key="Tax sub-totals", val=[("Taxable amount", MANDATORY, True),
                                                 ("Tax amount", invoice_tax["TaxType"], True),
                                                 ("TAX percentage", invoice_tax["TaxType"], True)])
        self.__parent("Line extension amount")
        self.__parent(key="Tax exclusive amount", val=invoice_total["TotalExclusiveTAX"], mandatory=True)  # MANDATORY
        self.__parent("Allowances amount")
        self.__parent("Charge amount")
        self.__parent("Prepaid amount")
        self.__parent(key="Rounding", val=invoice_total["Rounding"])
        self.__parent("Amount for payment")

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
                     ("Tax percent", MANDATORY, True),
                     ("Item price", MANDATORY, True)]
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
            self.info_dict[key] = MANDATORY
        else:
            pass

    def __child(self, key_vals=None):
        parent_val = {}
        for i in range(len(key_vals)):
            key, val, mandatory = key_vals[i]
            if val != EMP:
                parent_val[key] = val
            elif mandatory:
                parent_val[key] = MANDATORY
            else:
                pass

        for key, value in parent_val.items():
            if parent_val[key] not in [EMP, MANDATORY]:
                return parent_val
        return EMP


if __name__ == '__main__':
    pass
