def conditional_format(sheetId, formula, startColumnIndex, endColumnIndex, startRowIndex, endRowIndex):
    """Changes the conditional formatting to 'formula' for cells in the specified rectangle"""
    return {
        "addConditionalFormatRule": {
            "rule": {
                "ranges": [
                    {
                        "sheetId": sheetId,
                        "startColumnIndex": startColumnIndex,
                        "endColumnIndex": endColumnIndex,
                        "startRowIndex": startRowIndex,
                        "endRowIndex": endRowIndex
                    }
                ],
                "booleanRule": {
                    "condition": {
                        "type": "CUSTOM_FORMULA",
                        "values": [
                            {
                                "userEnteredValue": formula
                            }
                        ]
                    },
                    "format": {
                        "backgroundColor": {
                            "red": 0.79,
                            "green": 0.86,
                            "blue": 0.97
                        }


                    }
                }
            },
            "index": 0
        }
    }


def number_format(sheetId, pattern, startColumnIndex, endColumnIndex, startRowIndex, endRowIndex):
    """Changes the number format to 'pattern' for cells in the specified rectangle"""
    return {
        "repeatCell": {
            "range": {
                "sheetId": sheetId,
                "startColumnIndex": startColumnIndex,
                "endColumnIndex": endColumnIndex,
                "startRowIndex": startRowIndex,
                "endRowIndex": endRowIndex
            },
            "cell": {
                "userEnteredFormat": {
                    "numberFormat": {
                        "type": "NUMBER",
                        "pattern": pattern
                    }
                }
            },
            "fields": "userEnteredFormat.numberFormat"
        }
    }


def bold_format(sheetId, startColumnIndex, endColumnIndex, startRowIndex, endRowIndex):
    """Changes the text format to bold for cells in the specified rectangle"""
    return {
        "repeatCell": {
            "range": {
                "sheetId": sheetId,
                "startColumnIndex": startColumnIndex,
                "endColumnIndex": endColumnIndex,
                "startRowIndex": startRowIndex,
                "endRowIndex": endRowIndex

            },
            "cell": {
                "userEnteredFormat": {
                    "textFormat": {
                        "bold": True
                    }
                }
            },
            "fields": "userEnteredFormat.textFormat"
        }
    }
