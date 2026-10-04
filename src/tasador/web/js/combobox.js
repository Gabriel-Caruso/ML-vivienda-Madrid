// Desplegable en el que se puede escribir para filtrar (patrón combobox de ARIA).
// El filtro ignora tildes y mayúsculas: "aguilas" encuentra "Águilas".

function normalizar(texto) {
  return texto.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
}

export class Combobox {
  // nombre: nombre del campo (district, neighbourhood); el input se llama campo-<nombre>.
  constructor(contenedor, nombre, alCambiar) {
    this.nombre = nombre;
    this.alCambiar = alCambiar;
    this.opciones = [];
    this.visibles = [];
    this.activa = -1;
    this.valorElegido = "";
    this.textoSinCoincidencias = "";

    this.entrada = document.createElement("input");
    this.entrada.type = "text";
    this.entrada.id = `campo-${nombre}`;
    this.entrada.name = nombre;
    this.entrada.autocomplete = "off";
    this.entrada.setAttribute("role", "combobox");
    this.entrada.setAttribute("aria-autocomplete", "list");
    this.entrada.setAttribute("aria-expanded", "false");
    this.entrada.setAttribute("aria-controls", `lista-${nombre}`);
    this.entrada.setAttribute("aria-describedby", `error-${nombre}`);

    this.lista = document.createElement("ul");
    this.lista.id = `lista-${nombre}`;
    this.lista.setAttribute("role", "listbox");
    this.lista.hidden = true;

    contenedor.append(this.entrada, this.lista);

    this.entrada.addEventListener("input", this.alEscribir.bind(this));
    this.entrada.addEventListener("keydown", this.alPulsarTecla.bind(this));
    this.entrada.addEventListener("focus", this.alEnfocar.bind(this));
    this.entrada.addEventListener("blur", this.alSalir.bind(this));
    this.lista.addEventListener("mousedown", this.alPulsarRaton.bind(this));
  }

  // opciones: [{ valor, texto }]. Conserva la elección si sigue disponible.
  establecerOpciones(opciones) {
    this.opciones = opciones;
    const elegida = this.buscarPorValor(this.valorElegido);
    if (elegida) {
      this.entrada.value = elegida.texto;
    } else {
      this.limpiar(false);
    }
  }

  establecerTextos(marcador, sinCoincidencias) {
    this.entrada.placeholder = marcador;
    this.textoSinCoincidencias = sinCoincidencias;
  }

  habilitar(habilitado) {
    this.entrada.disabled = !habilitado;
  }

  valor() {
    return this.valorElegido;
  }

  limpiar(avisar = true) {
    const habiaValor = this.valorElegido !== "";
    this.valorElegido = "";
    this.entrada.value = "";
    if (avisar && habiaValor) {
      this.alCambiar("");
    }
  }

  buscarPorValor(valor) {
    for (const opcion of this.opciones) {
      if (opcion.valor === valor) {
        return opcion;
      }
    }
    return null;
  }

  filtrar(texto) {
    const buscado = normalizar(texto.trim());
    const visibles = [];
    for (const opcion of this.opciones) {
      if (normalizar(opcion.texto).includes(buscado)) {
        visibles.push(opcion);
      }
    }
    return visibles;
  }

  abrir() {
    this.visibles = this.filtrar(this.entrada.value);
    this.activa = this.visibles.length > 0 ? 0 : -1;
    this.dibujarLista();
    this.lista.hidden = false;
    this.entrada.setAttribute("aria-expanded", "true");
  }

  cerrar() {
    this.lista.hidden = true;
    this.entrada.setAttribute("aria-expanded", "false");
    this.entrada.removeAttribute("aria-activedescendant");
  }

  dibujarLista() {
    this.lista.replaceChildren();
    if (this.visibles.length === 0) {
      const vacio = document.createElement("li");
      vacio.textContent = this.textoSinCoincidencias;
      vacio.setAttribute("aria-disabled", "true");
      this.lista.append(vacio);
      this.entrada.removeAttribute("aria-activedescendant");
      return;
    }
    for (let posicion = 0; posicion < this.visibles.length; posicion += 1) {
      const elemento = document.createElement("li");
      elemento.id = `${this.lista.id}-${posicion}`;
      elemento.setAttribute("role", "option");
      elemento.dataset.posicion = String(posicion);
      elemento.textContent = this.visibles[posicion].texto;
      const activa = posicion === this.activa;
      elemento.setAttribute("aria-selected", activa ? "true" : "false");
      this.lista.append(elemento);
      if (activa) {
        this.entrada.setAttribute("aria-activedescendant", elemento.id);
        elemento.scrollIntoView({ block: "nearest" });
      }
    }
  }

  elegir(opcion) {
    this.entrada.value = opcion.texto;
    this.cerrar();
    if (opcion.valor !== this.valorElegido) {
      this.valorElegido = opcion.valor;
      this.alCambiar(opcion.valor);
    }
  }

  alEscribir() {
    if (this.valorElegido !== "") {
      this.valorElegido = "";
      this.alCambiar("");
    }
    this.abrir();
  }

  alEnfocar() {
    this.abrir();
  }

  alSalir() {
    this.cerrar();
    // Un texto escrito que coincide exactamente con una opción cuenta como elección
    if (this.valorElegido === "") {
      const escrito = normalizar(this.entrada.value.trim());
      for (const opcion of this.opciones) {
        if (normalizar(opcion.texto) === escrito && escrito !== "") {
          this.elegir(opcion);
          return;
        }
      }
    }
  }

  alPulsarRaton(evento) {
    const elemento = evento.target.closest("[role=option]");
    if (elemento) {
      evento.preventDefault();
      this.elegir(this.visibles[Number(elemento.dataset.posicion)]);
    }
  }

  alPulsarTecla(evento) {
    if (evento.key === "ArrowDown" || evento.key === "ArrowUp") {
      evento.preventDefault();
      if (this.lista.hidden) {
        this.abrir();
        return;
      }
      if (this.visibles.length === 0) {
        return;
      }
      const paso = evento.key === "ArrowDown" ? 1 : -1;
      this.activa = (this.activa + paso + this.visibles.length) % this.visibles.length;
      this.dibujarLista();
    } else if (evento.key === "Enter") {
      if (!this.lista.hidden && this.activa >= 0) {
        evento.preventDefault();
        this.elegir(this.visibles[this.activa]);
      }
    } else if (evento.key === "Escape") {
      this.cerrar();
    }
  }
}
