// Mostrar menú al cargar la página
async function hacerPedido(id) {
    let mesa = document.getElementById("mesaInput").value.trim();
    if (!mesa) {
        alert("⚠️ Por favor ingresa el número de mesa o nombre antes de pedir.");
        return;
    }

    let pedido = [];

function agregarPedido(nombre, precio) {
  pedido.push({ nombre, precio });
  alert(`${nombre} agregado al pedido`);
}

function enviarPedido() {
  if (pedido.length === 0) {
    alert("No hay platos en el pedido");
    return;
  }

  fetch("/enviar_pedido", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(pedido)
  })
  .then(res => res.json())
  .then(data => {
    alert(data.mensaje);
    pedido = [];
  });
}

    let data = await res.json();
    let chat = document.getElementById("chatbox");
    chat.innerHTML += `<p><b>Bot:</b> ${data.mensaje}</p>`;
    chat.scrollTop = chat.scrollHeight;

    cargarMenu();
}
