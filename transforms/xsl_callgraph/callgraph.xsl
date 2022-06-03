<?xml version="1.0" encoding="utf-8" ?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
	<xsl:template match="/">
		<CallGraph>
			<xsl:for-each select="//functionDefinition">
				<xsl:element name="{@name}">
					<xsl:for-each select="descendant::functionCall/name/expression/lvalue/base/variableUse">
						<xsl:element name="{@name}" />
					</xsl:for-each>
				</xsl:element>
			</xsl:for-each>
		</CallGraph>
	</xsl:template>
</xsl:stylesheet>
