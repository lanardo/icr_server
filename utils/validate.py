from utils.settings import *
import utils.text_annos_manage as manager

EMP = ""


class Validate:
    def __init__(self):
        pass

    def __validate_lines(self, template, product_lines):
        components = template['info']['InvoiceLines']['components']
        idx_quantity, idx_price, idx_total, idx_discount, idx_fee = None, None, None, None, None
        for component in components:
            if component['meaning'] == "Quantity":
                idx_quantity = components.index(component)
            elif component['meaning'] == "Price":
                idx_price = components.index(component)
            elif component['meaning'] == "Discount":
                idx_discount = components.index(component)
            elif component['meaning'] == "Fee":
                idx_fee = components.index(component)
            elif component['meaning'] == "TotalLineAmount":
                idx_total = components.index(component)

        if idx_quantity is None or idx_price is None or idx_total is None:
            return

        sum_of_total = 0  # here meaning : total = quan x price x (1-disc)
        sum_of_disc = 0
        sum_of_fees = 0
        true_cnt = 0
        validated_lines = []
        for value_list in product_lines:
            if idx_discount is None:
                disc = 100
            else:
                disc = manager.str2val(value_list[idx_discount])
            if idx_fee is None:
                fee = 0.0
            else:
                fee = manager.str2val(value_list[idx_fee])

            total = manager.str2val(value_list[idx_total])
            quant = manager.str2val(value_list[idx_quantity])
            price = manager.str2val(value_list[idx_price])

            try:
                if quant == -1 and price != -1 and total != -1:
                    quant = total / (price * (100-disc) / 100)
                    value_list[idx_quantity] = "{:.1f}".format(quant)
                if quant != -1 and price == -1 and total != -1:
                    price = total / (quant * (100-disc) / 100)
                    value_list[idx_price] = "{:.2f}".format(price)
                if quant != -1 and price != -1 and total == -1:
                    total = quant * (price * (100-disc) / 100)
                    value_list[idx_total] = "{:.2f}".format(total)
            except Exception as e:
                if total != -1:
                    price = total * 100 / (100-disc)
                    quant = 1.0
                elif price != -1:
                    total = (price * (100-disc) / 100) * quant
                    quant = 1.0
                else:
                    continue

            if self.__equantl(total, quant * price * (100-disc) / 100):
                true_cnt += 1
                sum_of_total += total
                sum_of_disc += quant * price * disc / 100
                sum_of_fees += fee

            validated_lines.append(value_list)

        if true_cnt == len(product_lines):
            validated = True
            lineTotal = sum_of_total + sum_of_disc - sum_of_fees
            sumOfDisc = sum_of_disc
            sumOfFees = sum_of_fees
            lines = validated_lines
        else:
            validated = False
            lineTotal = -1
            sumOfDisc = -1
            sumOfFees = -1
            lines = product_lines

        return {
            'validated': validated,
            'lineTotal': lineTotal,
            'sumOfDisc': sumOfDisc,
            'sumOfFees': sumOfFees,
            'lines': lines
        }

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
            if 'TaxValue' not in tax.keys() or 'TaxType' not in tax.keys():
                v_tax['TaxValue'] = 0.0
                v_tax['TaxType'] = 0.0
            else:
                v_tax['TaxValue'] = manager.str2val(tax['TaxValue'])
                v_tax['TaxType'] = manager.str2val(tax['TaxType'])

        return v_tax

    def __equantl(self, value1, value2):
        return math.fabs(value1 - value2) <= 1.0

    def __validate_total(self, total, v_lines, v_tax):
        rounding = manager.str2val(total['Rounding'])
        total_inc = manager.str2val(total['TotalInclusiveTAX'])
        total_exc = manager.str2val(total['TotalExclusiveTAX'])

        tax_val, tax_type = v_tax['TaxValue'], v_tax['TaxType']

        """ validteing Rule
            # v_total,
            # total_exc, total_exc, rounding
            # tax_val, tax_type
    
            # total_exc = total_exc + tax_val ( + rounding )
            # tax_val = total_exc * tax_type / 100
            # v_total = total_exc
        """
        # from validated_lines
        if v_lines['validated']:
            total_exc = v_lines['lineTotal'] + v_lines['sumOfFees'] - v_lines['sumOfDisc']
            if tax_type in [25, 15, 10]:
                if not self.__equantl(tax_val, (tax_type / 100) * total_exc):
                    tax_val = (tax_type / 100) * total_exc
            else:
                tax_type = round((tax_val * 100) / total_exc, 0)

            if rounding == total_inc - round(total_inc) and total_exc * 2 > total_inc > total_exc:
                tax_val = total_inc - total_exc
                tax_type = tax_val * 100 / total_exc

            total_inc = total_exc + tax_val

        # first check the tax_type and tax_value
        if tax_type in [25, 15, 10]:
            if self.__equantl(total_inc, total_exc * (tax_type + 100) / 100):
                if not self.__equantl(tax_val, total_exc * tax_type / 100):
                    tax_val = total_exc * tax_type / 100
        else:
            if self.__equantl(total_inc, total_exc + tax_val):
                tax_type = tax_val * 100 / total_exc

        # check the total_inc and total_exc
        if self.__equantl(total_exc * tax_type / 100, tax_val):
            total_inc = total_exc + tax_val

        # validate
        ret = True
        if self.__equantl(total_inc, total_exc + tax_val) and \
                self.__equantl(tax_val, total_exc * tax_type / 100):

            rounding = round(total_inc) - (total_exc + tax_val)
            total_inc = round(total_exc + tax_val + rounding)
            tax_type = int(round(tax_type))
            ret = False

        v_tax = {'TaxValue': round(tax_val, 2), 'TaxType': round(tax_type, 0)}
        v_total = {'Rounding': round(rounding, 2),
                   'TotalInclusiveTAX': round(total_inc, 2),
                   'TotalExclusiveTAX': round(total_exc, 2),

                   'LineExtensionAmount': round(v_lines['lineTotal'], 2),
                   'SumOfDiscount': round(v_lines['sumOfDisc'], 2),
                   'SumOfFees': round(v_lines['sumOfFees'], 2)
                   }

        return ret, v_tax, v_total, v_lines['lines']

    def validate(self, template, invoice_info):
        lines = invoice_info['invoice_lines']
        total = invoice_info['invoice_total']
        tax = invoice_info['invoice_tax']

        v_lines = self.__validate_lines(template=template, product_lines=lines)
        v_tax = self.__validate_tax(template=template, tax=tax)

        suc, v_tax, v_total, product_lines = self.__validate_total(total=total, v_lines=v_lines, v_tax=v_tax)

        validated_info = copy.deepcopy(invoice_info)
        validated_info['invoice_lines'] = product_lines
        validated_info['invoice_tax'] = v_tax
        validated_info['invoice_total'] = v_total
        validated_info['validated'] = suc

        return validated_info
