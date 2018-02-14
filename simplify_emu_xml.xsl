<?xml version="1.0" encoding="UTF-8"?>
<!-- This transform generates a simplified form of EMu's default
XML output. Nodes with 'name' attributes get renamed with the 'name', nodes without names get preserved as-is:

        <table name='ecatalogue'>
            <tuple>
                <atom name='irn'>1234</atom>
            </tuple>
        </table>

becomes

        <ecatalogue>
            <tuple>
                <irn>1234</irn>
            </tuple>
        </ecatalogue>
-->
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xs="http://www.w3.org/2001/XMLSchema"
    exclude-result-prefixes="xs"
    version="1.0">
    <xsl:output method="xml"/>
    
    <xsl:template match="*[@name]">
        <xsl:element name="{@name}">
            <xsl:apply-templates />
        </xsl:element>
    </xsl:template>
    
    <xsl:template match="node() | @*">
       <xsl:copy>
           <xsl:apply-templates select="node() | @*"/>
       </xsl:copy>
    </xsl:template>
    
</xsl:stylesheet>
