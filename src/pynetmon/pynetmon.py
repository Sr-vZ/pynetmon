import time
import socket
from socket import AF_INET
from socket import SOCK_DGRAM
from socket import SOCK_STREAM
import threading

import psutil
import asciichartpy as acp

from rich import print
from rich import box
from rich.live import Live
from rich.panel import Panel
from rich.layout import Layout
from rich.console import Console
from rich.prompt import Prompt
from rich.align import Align
from rich.table import Table

from pynput import keyboard as kb

AD = "-"
AF_INET6 = getattr(socket, "AF_INET6", object())
proto_map = {
    (AF_INET, SOCK_STREAM): "tcp",
    (AF_INET6, SOCK_STREAM): "tcp6",
    (AF_INET, SOCK_DGRAM): "udp",
    (AF_INET6, SOCK_DGRAM): "udp6",
}

default_config = {"graph_width": 70, "panel_border": "#d600ff"}
global exit_script


def tcp_connections():
    proc_names = {}
    tcp_details = []
    try:
        for p in psutil.process_iter(["pid", "name"]):
            proc_names[p.info["pid"]] = p.info["name"]
    except PermissionError or AttributeError:
        pass
    for c in psutil.net_connections(kind="inet4"):
        laddr = "%s:%s" % (c.laddr)
        raddr = ""
        if c.raddr:
            raddr = "%s:%s" % (c.raddr)
        name = proc_names.get(c.pid, "?") or ""
        tcp_details.append(
            {
                "conn_type": proto_map[(c.family, c.type)],
                "local_addr": laddr,
                "remote_addr": raddr or AD,
                "status": c.status,
                "pid": c.pid or AD,
                "name": name[:15],
            }
        )
    return tcp_details


def net_usage():
    net_stat = psutil.net_io_counters()
    net_in_1 = net_stat.bytes_recv
    net_out_1 = net_stat.bytes_sent
    time.sleep(0.1)
    net_stat = psutil.net_io_counters()
    net_in_2 = net_stat.bytes_recv
    net_out_2 = net_stat.bytes_sent

    net_in = round((net_in_2 - net_in_1) * 10 / 1024 / 1024, 3)
    net_out = round((net_out_2 - net_out_1) * 10 / 1024 / 1024, 3)

    return net_in, net_out


def draw_graph_panel(sent_data, graph_name, color):
    acp_config = {
        "width": default_config["graph_width"],
        # "height": 10,
        "format": "{:8.2f} MB/s",
    }
    return Panel(
        Align.left(acp.plot(sent_data, acp_config), vertical="bottom"),
        title=f"[bold][yellow]{graph_name}[/bold][/yellow]",
        border_style="#d600ff",
        style=color,
    )


def create_tcp_table():
    tcp_data = tcp_connections()
    table = Table(
        title="Open Ports",
        box=box.ROUNDED,
        border_style=default_config["panel_border"],
        title_style="bold yellow",
    )
    headers = [
        "Proto",
        "Local address",
        "Remote address",
        "Status",
        "PID",
        "Program name",
    ]
    for h in headers:
        table.add_column(h)

    for d in tcp_data:
        table.add_row(
            d["conn_type"],
            d["local_addr"],
            d["remote_addr"],
            d["status"],
            str(d["pid"]),
            d["name"],
        )
    return table


def user_control(key):
    # if key == Key.tab:
    #     print("good")

    # if key != Key.tab:
    #     print("try again")

    # by pressing 'delete' button
    # you can terminate the loop

    if key == kb.Key.q:
        exit_script = True
        return False


def main():
    exit_script = False
    sent_buffer = []
    recv_buffer = []
    layout = Layout()
    # Divide the "screen" in to three parts
    layout.split(
        Layout(name="header", size=3),
        Layout(
            name="main",
            ratio=1,
        ),
        Layout(name="footer", size=3),
    )
    layout["main"].split_row(Layout(name="info"), Layout(name="graphs"))
    layout["graphs"].split_column(Layout(name="recv_graph"), Layout(name="sent_graph"))
    layout["info"].split(Layout(name="net_usage", size=3), Layout(name="ports_table"))

    layout["header"].update(
        Panel(
            Align.center("[bold][yellow]Python Network Monitoring[/yellow][/bold]"),
            border_style=default_config["panel_border"],
        )
    )
    layout["footer"].update(
        Panel(
            Align.left("[bold][yellow]Q to Quit[/yellow][/bold]"),
            # name=Prompt.ask(
            #     "Enter your name", choices=["Paul", "Jessica", "Duncan"], default="Paul"
            # ),
            title="Controls",
            border_style=default_config["panel_border"],
        )
    )
    # kb_listener = kb.Listener(on_press=user_control)
    with Live(layout, refresh_per_second=10, screen=True) as live:
        # for i in range(1000):
        while exit_script == False:
            # time.sleep(0.1)
            # recv_bytes, sent_bytes = get_net_stats()
            recv_bytes, sent_bytes = net_usage()
            sent_buffer.append(sent_bytes)
            recv_buffer.append(recv_bytes)
            # d.append(get_net_stats())
            sent_buffer = sent_buffer[-default_config["graph_width"] : :]
            recv_buffer = recv_buffer[-default_config["graph_width"] : :]
            # pass only X latest
            layout["recv_graph"].update(
                draw_graph_panel(recv_buffer, "Data Received Graph", "#00ff9f")
            )
            layout["sent_graph"].update(
                draw_graph_panel(sent_buffer, "Data Sent Graph", "#00b8ff")
            )
            layout["net_usage"].update(
                Panel(
                    Align.center(
                        f"IN: [bold][green]{recv_bytes:4.3f}[/green][/bold] MB/s OUT: [bold][red]{sent_bytes:4.3f}[/red][/bold] MB/s"
                    ),
                    border_style=default_config["panel_border"],
                    title="[bold][yellow]Network Stats[/bold][/yellow]",
                )
            )
            layout["ports_table"].update(
                # Panel(
                #     Align.center(create_tcp_table()),
                #     border_style=default_config["panel_border"],
                #     title="[bold][yellow]Open Ports[/bold][/yellow]",
                # )
                Align.center(create_tcp_table(), vertical="middle")
            )

            # Collect all event until released
        # with kb.Listener(on_press=user_control) as listener:
        #     listener.join()


if __name__ == "__main__":
    # ui_thread = threading.Thread(target=main)
    # ui_thread.start()

    # with kb.Listener(on_release == user_control) as kb_listener:
    #     kb_listener.join()
    main()
    # create_tcp_table()
