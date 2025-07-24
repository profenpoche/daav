import { ClassicPreset, NodeEditor } from "rete";
import { Schemes } from "../workflow-editor";
import { SocketComponent } from "src/app/components/sockets/socket-component/socket.component";
import { CustomConnectionComponent } from "src/app/components/connections/connections.component";
import { DeepSocketComponent } from "src/app/components/sockets/deep-socket-component/deep-socket.component";
import { FlatSocketComponent } from "src/app/components/sockets/flat-socket-component/flat-socket.component";
import { GlobalSocketComponent } from "src/app/components/sockets/global-socket-component/global-socket.component";




export abstract class BaseSocket extends ClassicPreset.Socket {

  getSocketComponent(): any{
    return SocketComponent;
  }

  getConnectionComponent(){
    return CustomConnectionComponent;
  }
}




export class FlatObjectSocket extends BaseSocket {
  constructor() {
    super("FlatObjectSocket");
  }
  isCompatibleWith(socket: Sockets) {
    return socket instanceof FlatObjectSocket || socket instanceof AllSocket;
  }
  override getSocketComponent(){
    return FlatSocketComponent;
  }
}

export class DeepObjectSocket extends BaseSocket {
  constructor() {
    super("DeepObjectSocket");
  }

  isCompatibleWith(socket: Sockets) {
    return socket instanceof DeepObjectSocket || socket instanceof AllSocket;
  }

  override getSocketComponent(){
    return DeepSocketComponent;
  }

}

export class LrsObjectSocket extends BaseSocket {
  constructor() {
    super("LrsObjectSocket");
  }

  isCompatibleWith(socket: Sockets) {
    return (socket instanceof LrsObjectSocket || socket instanceof DeepObjectSocket || socket instanceof AllSocket);
  }
}


export class AllSocket extends BaseSocket {
  constructor() {
    super("AllSocket");
  }

  isCompatibleWith(socket: Sockets) {
    return (socket instanceof BaseSocket);
  }

  override getSocketComponent(){
    return GlobalSocketComponent;
  }
}


export class SimpleFieldSocket extends BaseSocket {
  constructor() {
    super("SimpleFieldSocket");
  }

  isCompatibleWith(socket: Sockets) {
    return socket instanceof SimpleFieldSocket || socket instanceof AllSocket;
  }
}

export type Sockets = SimpleFieldSocket | LrsObjectSocket | DeepObjectSocket | FlatObjectSocket;
export type Input = ClassicPreset.Input<Sockets>;
export type Output = ClassicPreset.Output<Sockets>;


export function getConnectionSockets(
  editor: NodeEditor<Schemes>,
  connection: Schemes["Connection"]
) {
  const source = editor.getNode(connection.source);
  const target = editor.getNode(connection.target);

  const output =
    source &&
    (source.outputs as Record<string, Input>)[connection.sourceOutput];
  const input =
    target && (target.inputs as unknown as Record<string, Output>)[connection.targetInput];

  return {
    source: output?.socket,
    target: input?.socket
  };
}
