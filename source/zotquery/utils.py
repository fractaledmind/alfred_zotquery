#!/usr/bin/python
# encoding: utf-8
#
# Copyright © 2014 stephen.margheim@gmail.com
#
# MIT Licence. See http://opensource.org/licenses/MIT
#
# Created on 17-05-2014
#
from __future__ import unicode_literals

# Standard Library
import unicodedata
import subprocess
import functools
import os
import re

from workflow import Workflow

WF = Workflow()


ASCII_REPLACEMENTS = {
    'À': 'A',
    'Á': 'A',
    'Â': 'A',
    'Ã': 'A',
    'Ä': 'A',
    'Å': 'A',
    'Æ': 'AE',
    'Ç': 'C',
    'È': 'E',
    'É': 'E',
    'Ê': 'E',
    'Ë': 'E',
    'Ì': 'I',
    'Í': 'I',
    'Î': 'I',
    'Ï': 'I',
    'Ð': 'D',
    'Ñ': 'N',
    'Ò': 'O',
    'Ó': 'O',
    'Ô': 'O',
    'Õ': 'O',
    'Ö': 'O',
    'Ø': 'O',
    'Ù': 'U',
    'Ú': 'U',
    'Û': 'U',
    'Ü': 'U',
    'Ý': 'Y',
    'Þ': 'Th',
    'ß': 'ss',
    'à': 'a',
    'á': 'a',
    'â': 'a',
    'ã': 'a',
    'ä': 'a',
    'å': 'a',
    'æ': 'ae',
    'ç': 'c',
    'è': 'e',
    'é': 'e',
    'ê': 'e',
    'ë': 'e',
    'ì': 'i',
    'í': 'i',
    'î': 'i',
    'ï': 'i',
    'ð': 'd',
    'ñ': 'n',
    'ò': 'o',
    'ó': 'o',
    'ô': 'o',
    'õ': 'o',
    'ö': 'o',
    'ø': 'o',
    'ù': 'u',
    'ú': 'u',
    'û': 'u',
    'ü': 'u',
    'ý': 'y',
    'þ': 'th',
    'ÿ': 'y',
    'Ł': 'L',
    'ł': 'l',
    'Ń': 'N',
    'ń': 'n',
    'Ņ': 'N',
    'ņ': 'n',
    'Ň': 'N',
    'ň': 'n',
    'Ŋ': 'ng',
    'ŋ': 'NG',
    'Ō': 'O',
    'ō': 'o',
    'Ŏ': 'O',
    'ŏ': 'o',
    'Ő': 'O',
    'ő': 'o',
    'Œ': 'OE',
    'œ': 'oe',
    'Ŕ': 'R',
    'ŕ': 'r',
    'Ŗ': 'R',
    'ŗ': 'r',
    'Ř': 'R',
    'ř': 'r',
    'Ś': 'S',
    'ś': 's',
    'Ŝ': 'S',
    'ŝ': 's',
    'Ş': 'S',
    'ş': 's',
    'Š': 'S',
    'š': 's',
    'Ţ': 'T',
    'ţ': 't',
    'Ť': 'T',
    'ť': 't',
    'Ŧ': 'T',
    'ŧ': 't',
    'Ũ': 'U',
    'ũ': 'u',
    'Ū': 'U',
    'ū': 'u',
    'Ŭ': 'U',
    'ŭ': 'u',
    'Ů': 'U',
    'ů': 'u',
    'Ű': 'U',
    'ű': 'u',
    'Ŵ': 'W',
    'ŵ': 'w',
    'Ŷ': 'Y',
    'ŷ': 'y',
    'Ÿ': 'Y',
    'Ź': 'Z',
    'ź': 'z',
    'Ż': 'Z',
    'ż': 'z',
    'Ž': 'Z',
    'ž': 'z',
    'ſ': 's',
    'Α': 'A',
    'Β': 'B',
    'Γ': 'G',
    'Δ': 'D',
    'Ε': 'E',
    'Ζ': 'Z',
    'Η': 'E',
    'Θ': 'Th',
    'Ι': 'I',
    'Κ': 'K',
    'Λ': 'L',
    'Μ': 'M',
    'Ν': 'N',
    'Ξ': 'Ks',
    'Ο': 'O',
    'Π': 'P',
    'Ρ': 'R',
    'Σ': 'S',
    'Τ': 'T',
    'Υ': 'U',
    'Φ': 'Ph',
    'Χ': 'Kh',
    'Ψ': 'Ps',
    'Ω': 'O',
    'α': 'a',
    'β': 'b',
    'γ': 'g',
    'δ': 'd',
    'ε': 'e',
    'ζ': 'z',
    'η': 'e',
    'θ': 'th',
    'ι': 'i',
    'κ': 'k',
    'λ': 'l',
    'μ': 'm',
    'ν': 'n',
    'ξ': 'x',
    'ο': 'o',
    'π': 'p',
    'ρ': 'r',
    'ς': 's',
    'σ': 's',
    'τ': 't',
    'υ': 'u',
    'φ': 'ph',
    'χ': 'kh',
    'ψ': 'ps',
    'ω': 'o',
    'А': 'A',
    'Б': 'B',
    'В': 'V',
    'Г': 'G',
    'Д': 'D',
    'Е': 'E',
    'Ж': 'Zh',
    'З': 'Z',
    'И': 'I',
    'Й': 'I',
    'К': 'K',
    'Л': 'L',
    'М': 'M',
    'Н': 'N',
    'О': 'O',
    'П': 'P',
    'Р': 'R',
    'С': 'S',
    'Т': 'T',
    'У': 'U',
    'Ф': 'F',
    'Х': 'Kh',
    'Ц': 'Ts',
    'Ч': 'Ch',
    'Ш': 'Sh',
    'Щ': 'Shch',
    'Ъ': "'",
    'Ы': 'Y',
    'Ь': "'",
    'Э': 'E',
    'Ю': 'Iu',
    'Я': 'Ia',
    'а': 'a',
    'б': 'b',
    'в': 'v',
    'г': 'g',
    'д': 'd',
    'е': 'e',
    'ж': 'zh',
    'з': 'z',
    'и': 'i',
    'й': 'i',
    'к': 'k',
    'л': 'l',
    'м': 'm',
    'н': 'n',
    'о': 'o',
    'п': 'p',
    'р': 'r',
    'с': 's',
    'т': 't',
    'у': 'u',
    'ф': 'f',
    'х': 'kh',
    'ц': 'ts',
    'ч': 'ch',
    'ш': 'sh',
    'щ': 'shch',
    'ъ': "'",
    'ы': 'y',
    'ь': "'",
    'э': 'e',
    'ю': 'iu',
    'я': 'ia',
    # 'ᴀ': '',
    # 'ᴁ': '',
    # 'ᴂ': '',
    # 'ᴃ': '',
    # 'ᴄ': '',
    # 'ᴅ': '',
    # 'ᴆ': '',
    # 'ᴇ': '',
    # 'ᴈ': '',
    # 'ᴉ': '',
    # 'ᴊ': '',
    # 'ᴋ': '',
    # 'ᴌ': '',
    # 'ᴍ': '',
    # 'ᴎ': '',
    # 'ᴏ': '',
    # 'ᴐ': '',
    # 'ᴑ': '',
    # 'ᴒ': '',
    # 'ᴓ': '',
    # 'ᴔ': '',
    # 'ᴕ': '',
    # 'ᴖ': '',
    # 'ᴗ': '',
    # 'ᴘ': '',
    # 'ᴙ': '',
    # 'ᴚ': '',
    # 'ᴛ': '',
    # 'ᴜ': '',
    # 'ᴝ': '',
    # 'ᴞ': '',
    # 'ᴟ': '',
    # 'ᴠ': '',
    # 'ᴡ': '',
    # 'ᴢ': '',
    # 'ᴣ': '',
    # 'ᴤ': '',
    # 'ᴥ': '',
    'ᴦ': 'G',
    'ᴧ': 'L',
    'ᴨ': 'P',
    'ᴩ': 'R',
    'ᴪ': 'PS',
    'ẞ': 'Ss',
    'Ỳ': 'Y',
    'ỳ': 'y',
    'Ỵ': 'Y',
    'ỵ': 'y',
    'Ỹ': 'Y',
    'ỹ': 'y',
}


class TextUtils(object):

    ## Text Encoding  ---------------------------------------------------------

    def decode(self, text, encoding='utf-8', normalization='NFC'):
        """Convert `text` to unicode

        """
        if isinstance(text, basestring):
            if not isinstance(text, unicode):
                text = unicode(text, encoding)
        return unicodedata.normalize(normalization, text)

    def isascii(self, text):
        """Test if ``text`` contains only ASCII characters

        :param text: text to test for ASCII-ness
        :type text: ``unicode``
        :returns: ``True`` if ``text`` contains only ASCII characters
        :rtype: ``Boolean``
        """

        try:
            self.decode(text).encode('ascii')
        except UnicodeEncodeError:
            return False
        return True

    def fold_to_ascii(self, text, on_error='ignore'):
        """Convert non-ASCII characters to closest ASCII equivalent.

        :param text: text to convert
        :type text: ``unicode``
        :returns: text containing only ASCII characters
        :rtype: ``unicode``
        """
        if on_error not in ('backslashreplace', 'replace',
                            'ignore', 'xmlcharrefreplace'):
            on_error = 'ignore'
        if self.isascii(text):
            return text
        text = ''.join([ASCII_REPLACEMENTS.get(c, c)
                        for c in self.decode(text)])
        return unicode(unicodedata.normalize('NFKD',
                       text).encode('ascii', on_error)).strip()

    ## Text Formatting  -------------------------------------------------------

    def slugify(self, text, max_length=0, separator='_'):
        """ Make a slug from the given text """

        # text to unicode
        text = self.decode(text)

        # convert CamelCase to under_score
        text = self.convert_camel(text)

        # decode unicode ('Компьютер' = kompiuter)
        text = self.fold_to_ascii(text)

        # text back to unicode
        text = self.decode(text)

        # replace unwanted characters
            # replace ' with nothing instead with -
        text = re.sub(r'[\']+', '', text.lower())
        text = re.sub(r'[^-a-z0-9]+', '-', text.lower())

        # remove redundant -
        text = re.sub(r'-{2,}', '-', text).strip('-')

        # smart truncate if requested
        if max_length > 0:
            text = self.smart_truncate(text, max_length, '-')

        if separator != '-':
            text = text.replace('-', separator)

        return text

    def smart_truncate(self, text, max_len=0, separator=' '):
        """Truncate a text with intelligent options.

        :param text: text to convert
        :type text: ``unicode``
        :param max_len: length of characters in `text` to return
        :type max_len: ``int``
        :param separator: text to convert
        :type separator: ``unicode``
        :returns: text containing only ASCII characters
        :rtype: ``unicode``
        """

        text = self.decode(text).strip(separator)

        if not max_len:
            return text

        if len(text) < max_len:
            return text

        if separator not in text:
            return text[:max_len]

        truncated = ''
        for word in text.split(separator):
            if word:
                next_len = len(truncated) + len(word) + len(separator)
                if next_len <= max_len:
                    truncated += '{0}{1}'.format(word, separator)
        if not truncated:
            truncated = text[:max_len]
        return truncated.strip(separator)

    def convert_camel(self, camel_case):
        """Convert CamelCase to underscore_format."""
        camel_re = re.compile(r'((?<=[a-z0-9])[A-Z]|(?!^)[A-Z](?=[a-z]))')
        return camel_re.sub(r'_\1', self.decode(camel_case)).lower()

    def normalise_whitespace(s):
        """Returns a string that has at most one whitespace
        character between non-whitespace characters. We
        leave a few extra spaces because most NLP parsers
        don't tend to care.
        >>> normalise_whitespace(' hi   there')
        ' hi there'
        >>> normalise_whitespace('meh\n\n\f')
        'meh '
        """
        return re.sub(r'\s+', ' ', s)

    ## Clipboard  -------------------------------------------------------------

    def set_clipboard(self, data):
        """Set clipboard to `data`"""
        text = self.decode(data)
        self.subprocess(['pbcopy', 'w'], text)

    def get_clipboard(self):
        """Retrieve data from clipboard"""
        return self.subprocess(['pbpaste'])

    def subprocess(self, cmd, stdin=None):
        # Is command shell string or list of args?
        shell = True
        if isinstance(cmd, list):
            shell = False
        # Set shell lang to UTF8
        os.environ['LANG'] = 'en_US.UTF-8'
        # Open pipes
        proc = subprocess.Popen(cmd,
                                shell=shell,
                                stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        # Run command, with optional input
        if stdin:
            (stdout, stderr) = proc.communicate(input=stdin.encode('utf-8'))
        else:
            (stdout, stderr) = proc.communicate()
        # Convert newline delimited str into clean list
        output = filter(None, [s.strip()
                               for s in self.decode(stdout).split('\n')])
        if len(output) == 0:
            return None
        elif len(output) == 1:
            return output[0]
        else:
            return output

    ## File Searching ---------------------------------------------------------

    def find_name(self, name):  # pragma: no cover
        """Use `mdfind` to locate file given its ``name``.

        :param name: full name of desired file
        :type name: ``unicode`` or ``str``
        :returns: list of paths to named file
        :rtype: :class:`list`

        """
        cmd = ['mdfind',
               'kMDItemFSName={}'.format(name),
               '-onlyin',
               '/']
        output = subprocess.check_output(cmd)
        # Convert newline delimited str into clean list
        output = [s.strip() for s in self.decode(output).split('\n')]
        return filter(None, output)


def store_properties(the_class):
    class_instance = the_class()
    # prettify the class name for file name
    class_name = text.convert_camel(the_class.__name__)

    class NewClass(the_class):
        # read properties JSON file, if it exists
        properties = WF.stored_data(class_name)
        store = False
        # if no data has been written to disk yet
        if not properties:
            properties = {k: getattr(class_instance, k)
                          for (k, v) in the_class.__dict__.items()
                          if isinstance(v, property)}
            store = True
        # if any property has a null value
        elif None in properties.values():
            # re-run properties with null values
            null_props = {k: getattr(class_instance, k)
                          for k, v in properties.items()
                          if not v}
            properties.update(null_props)
            store = True
        # re-store new dictionary?
        if store:
            # store generated dictionary in JSON format
            WF.store_data(class_name, properties,
                          serializer='json')
        setattr(the_class, 'properties', properties)
    return NewClass


def stored_property(func):
    @property
    @functools.wraps(func)
    def func_wrapper(self):
        try:
            var = self.properties[func.__name__]
            if var:
                # property already written to disk
                return var
            else:
                # property written to disk as `null`
                return func(self)
        except AttributeError:
            # `self.me` does not yet exist
            return func(self)
        except KeyError:
            # `self.me` exists, but property is not a key
            return func(self)
    return func_wrapper


# aliases
text = TextUtils()


if __name__ == '__main__':
    pass
