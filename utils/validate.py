import math
import utils.text_annos_manage as manager
import copy

EMP = ""


class Validate:
    def __init__(self):
        pass

    def __validate_lines(self, template, product_lines):
        components = template['info']['InvoiceLines']['components']
        idx_quantity, idx_price, idx_total = None, None, None
        for component in components:
            if component['meaning'] == "Quantity":
                idx_quantity = components.index(component)
            elif component['meaning'] == "Price":
                idx_price = components.index(component)
            elif component['meaning'] == "TotalLineAmount":
                idx_total = components.index(component)

        if idx_quantity is None or idx_price is None or idx_total is None:
            return

        v_total = 0
        true_pos = 0
        v_lines = []
        for value_list in product_lines:
            qua = manager.str2val(value_list[idx_quantity])
            price = manager.str2val(value_list[idx_price])
            total = manager.str2val(value_list[idx_total])

            if qua == -1 and price != -1 and total != -1:
                qua = total / price
                value_list[idx_quantity] = "{:.1f}".format(qua)
            if qua != -1 and price == -1 and total != -1:
                price = total / qua
                value_list[idx_price] = "{:.2f}".format(price)
            if qua != -1 and price != -1 and total == -1:
                total = qua * price
                value_list[idx_total] = "{:.2f}".format(total)

            if total == qua * price:
                true_pos += 1
                v_total += total

            v_lines.append(value_list)

        if true_pos != len(product_lines):
            v_total = -1

        return v_lines, v_total

    def __validate_tax(self, template, tax):
        components = template['info']['TotalTAXs']['components']
        orientation = template['info']['TotalTAXs']['orientation']
        type = template['info']['TotalTAXs']['type']

        v_tax = {'TaxValue': -1,
                 'TaxType': -1}
        if type == "list":
            for t in tax:
                if t != EMP:
                    v_tax['TaxValue'] = manager.str2val(t)
                    v_tax['TaxType'] = manager.str2val(components[tax.index(t)]['meanning'])
                    break

        elif type == "dict" and orientation == "under":
            v_tax['TaxValue'] = manager.str2val(tax['TaxValue'])
            v_tax['TaxType'] = manager.str2val(tax['TaxType'])

        return v_tax

    def __equal(self, value1, value2):
        return math.fabs(value1 - value2) <= 1.0

    def __validate_total(self, total, line_total, v_tax):
        rounding = manager.str2val(total['Rounding'])
        total_inc = manager.str2val(total['TotalInclusiveTAX'])
        total_exc = manager.str2val(total['TotalExclusiveTAX'])
        tax_val, tax_type = v_tax['TaxValue'], v_tax['TaxType']

        # v_total,
        # total_exc, total_exc, rounding
        # tax_val, tax_type

        # total_exc = total_exc + tax_val ( + rounding )
        # tax_val = total_exc * tax_type / 100
        # v_total = total_exc

        if self.__equal(total_inc, total_exc + tax_val):
            tax_type = tax_val * 100 / total_exc

        elif self.__equal(total_inc, total_exc * (tax_type + 100) / 100):
            tax_val = total_exc * tax_type / 100

        elif self.__equal(total_exc * tax_type / 100, tax_val):
            total_inc = total_exc + tax_val

        elif self.__equal(total_inc, line_total + tax_val):
            total_exc = line_total
            tax_type = tax_val * 100 / total_exc

        elif self.__equal(line_total * tax_type / 100, tax_val):
            total_exc = line_total
            total_inc = round(total_exc + tax_val)

        elif rounding == total_inc - round(total_inc) and \
                total_exc * 2 > total_inc > total_exc and total_exc == line_total:
            tax_val = total_inc - total_exc
            tax_type = tax_val * 100 / total_exc

        if self.__equal(total_inc, total_exc + tax_val) and self.__equal(tax_val, total_exc * tax_type / 100):
            rounding = round(total_inc) - (total_exc + tax_val)
            total_inc = round(total_exc + tax_val + rounding)
            tax_type = int(round(tax_type))

            v_tax = {'TaxValue': round(tax_val, 2), 'TaxType': round(tax_type, 0)}
            v_total = {'Rounding': round(rounding, 2),
                       'TotalInclusiveTAX': round(total_inc, 2),
                       'TotalExclusiveTAX': round(total_exc, 2)}
            return True, v_tax, v_total
        else:
            return False, v_tax, total

    def validate(self, template, invoice_info):
        lines = invoice_info['invoice_lines']
        total = invoice_info['invoice_total']
        tax = invoice_info['invoice_tax']

        v_lines, line_total = self.__validate_lines(template=template, product_lines=lines)
        v_tax = self.__validate_tax(template=template, tax=tax)

        suc, v_tax, v_total = self.__validate_total(total=total, line_total=line_total, v_tax=v_tax)

        validated_info = copy.deepcopy(invoice_info)
        validated_info['invoice_lines'] = v_lines
        validated_info['invoice_tax'] = v_tax
        validated_info['invoice_total'] = v_total
        validated_info['validated'] = suc

        return validated_info
