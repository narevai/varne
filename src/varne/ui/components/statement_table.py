from varne.ui.components.tip import TIP_ATTRIBUTES


def logo_tile(kind: str, icon: str, mono: str, symbol: str) -> str:
    """The logo of a row of the statement in a tile of the colour of its side: the
    template of it, for the table of the browser to fill in. Its size is in the CSS."""
    return f"""
        <div class="logo-tile {kind}">
            <img v-if="{icon}" :src="{icon}" :class="{mono}" />
            <q-icon v-else :name="{symbol}" size="28px" class="faint" />
        </div>"""


# The application of a row: its logo, its name, and the containers it runs in.
APPLICATION_CELL = f"""
<q-td :props="props">
    <div class="cell-logo"
         :class="[props.row.more ? 'cursor-pointer' : '', props.row.nested ? 'row-nested' : '']">
        {logo_tile("logo-self", "props.row.icon", "''", "props.row.symbol || 'apps'")}
        <div>
            <div>{{{{ props.value }}}}</div>
            <div class="text-caption faint cell-caption">
                {{{{ props.row.containers }}}}
                <q-tooltip v-if="props.row.all_containers" class="seg-tip" @tip-attributes>
                    <table class="tip-table">
                        <tr v-for="(name, index) in props.row.all_containers.split('\\n')" :key="name">
                            <td class="key"><div>{{{{ index === 0 ? 'Containers' : '' }}}}</div></td>
                            <td class="value"><div>{{{{ name }}}}</div></td>
                        </tr>
                    </table>
                </q-tooltip>
            </div>
        </div>
    </div>
</q-td>
""".replace("@tip-attributes", TIP_ATTRIBUTES)

# The hosted service of a row: the logo of the service, never that of the application.
HOSTED_CELL = f"""
<q-td :props="props">
    <div class="cell-logo">
        <template v-if="props.row.hosted">
            {logo_tile("logo-hosted", "props.row.hosted_icon", "props.row.hosted_mono ? 'logo-mono' : ''", "'apps'")}
        </template>
        <span>{{{{ props.value }}}}</span>
    </div>
</q-td>
"""

DIFFERENCE_CELL = """
<q-td :props="props" :class="props.row.tone"><b>{{ props.value }}</b></q-td>
"""


def number_column(name: str, label: str) -> dict[str, str]:
    return {"name": name, "label": label, "field": name, "align": "right"}
