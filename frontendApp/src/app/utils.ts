import { ClassicPreset, NodeEditor } from "rete";
import { Schemes } from "./core/test-workflow-daav-test";
import { DeepObjectSocket, FlatObjectSocket, LrsObjectSocket, SimpleFieldSocket } from "./core/sockets/sockets";
type Sockets = FlatObjectSocket | DeepObjectSocket | LrsObjectSocket | SimpleFieldSocket;
type Input = ClassicPreset.Input<Sockets>;
type Output = ClassicPreset.Output<Sockets>;


/**
 * Retrieve the socket objects associated with the input and output connections of a node
 * @param editor Node Editor
 * @param connection
 * @returns
 */
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
      target && (source.outputs as Record<string, Output>)[connection.targetInput];

    return {
      source: output?.socket,
      target: input?.socket
    };
  }


