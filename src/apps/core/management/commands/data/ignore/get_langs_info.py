import requests

from ..languages import TWO_LETTERS_CODES

URL = 'https://cloud.appwrite.io/v1/locale/languages/'

APPWRITE_LANGUAGES = {}

FLAG_ICONS_PATH = 'apps/languages/images/flag_icons/'

if __name__ == '__main__':
    response = requests.get(URL)
    response_content = response.json()

    if response.status_code == 200:
        for lang_info in response_content['languages']:
            APPWRITE_LANGUAGES[lang_info['code']] = {
                'name': lang_info['name'],
                'nativeName': lang_info['nativeName'],
            }
    else:
        print(
            f'Error in fetching `APPWRITE_LANGUAGES` by url `{URL}` '
            f'(status code: {response.status_code})'
        )

    res = []
    not_found_counter = 0

    for isocode in TWO_LETTERS_CODES:
        language_isocode = isocode.split('-')[0]

        # add language_name_local info
        try:
            language_local = APPWRITE_LANGUAGES[language_isocode]['nativeName']
        except KeyError:
            try:
                language_local = APPWRITE_LANGUAGES[isocode.lower()]['nativeName']
            except KeyError:
                language_local = ''
                not_found_counter += 1

        # add flag_icon_path info
        flag_icon_path = (
            FLAG_ICONS_PATH + TWO_LETTERS_CODES[isocode]['country'].lower() + '.svg'
        )

        res.append(
            f"'{isocode}': {'{'}\n\t'language_name': '{TWO_LETTERS_CODES[isocode]['name']}',\n\t'name_local': '{language_local}',\n\t'country': '{TWO_LETTERS_CODES[isocode]['country']}',\n\t'country_cca3': '{TWO_LETTERS_CODES[isocode]['country_cca3']}',\n\t'flag_icon_path': '{flag_icon_path}',\n{'}'},"
        )

    print(
        '\n'.join(res),
        f'\nCodes not found in response content: {not_found_counter} (from {len(res)})',
    )

    file1 = open('langs_info.txt', 'w', encoding='utf-8')
    file1.write('\n'.join(res))
    file1.close()
