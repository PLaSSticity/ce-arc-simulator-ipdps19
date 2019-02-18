import django
from django.conf import settings
from django.template import Context
from django.template.engine import Engine


class HTMLProduct:
    """Generate an html page with links to individual results."""

    def __init__(self, options):
        self.options = options
        self.template = """
        <!DOCTYPE HTML>
        <html>
        <head>
        <title>
        {{ my_title|safe }}
        </title>
        </head>
        <body>
        {{ my_body|safe }}
        </body>
        </html>
        """

    def createHTMLFile(self, str_cmdLine):
        """Create the html file with embedded links."""
        str_title = "Products from " + self.options.output
        str_body = """<p></p>
                    <a href="output_table.html">Output data</a>
                    <p></p>
                    <p>
                    <a href="pintool_stats_table.html">Pintool stats table</a>
                    <p></p>
                    <p>
                    <a href="sim_stats_table.html">Simulator stats table</a>
                    <p></p>
                    <p>
                    <a href="mcpat/">McPat inputs and outputs</a>
                    <p></p>
                    <p>
                    <a href="energy_stats_table.html">Energy stats table</a>
                    <p></p>
                    <p>
                    <a href="absolute/index.html">Absolute bar graphs</a>
                    <p></p>
                    <p>
                    <a href="normalized/index.html">Normalized bar graphs</a>
                    <p></p>
                    <p>
                    <a href="stacked/index.html">Normalized stacked bar graphs</a>
                    <p></p>
                    <p>
                    <b>EXP command:</b><br>
                    <PRE>""" + str_cmdLine + """</PRE>"""

        if not self.options.generateEnergyStats:
            str_body = """<p></p>
                        <a href="output_table.html">Output data</a>
                        <p></p>
                        <p>
                        <a href="pintool_stats_table.html">Pintool stats table</a>
                        <p></p>
                        <p>
                        <a href="sim_stats_table.html">Simulator stats table</a>
                        <p></p>
                        <p>
                        <a href="mcpat/">McPat inputs and outputs</a>
                        <p></p>
                        <p>
                        <a href="absolute/index.html">Absolute bar graphs</a>
                        <p></p>
                        <p>
                        <a href="normalized/index.html">Normalized bar graphs</a>
                        <p></p>
                        <p>
                        <a href="stacked/index.html">Normalized stacked bar graphs</a>
                        <p></p>
                        <p>
                        <b>EXP command:</b><br>
                        <PRE>""" + str_cmdLine + """</PRE>"""

        htmSrc = self.__generate(str_title, str_body)
        htm = open("index.html", "w")
        htm.write(htmSrc)
        htm.close()

    def __generate(self, title, code):
        settings.configure()
        django.setup()
        template = Engine().from_string(self.template)
        c = Context({"my_title": title, "my_body": code})
        return template.render(c)
